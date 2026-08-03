import os
import itertools
import numpy as np
import yt
from unyt import unyt_array
from yt.utilities.orientation import Orientation
from yt.visualization.volume_rendering.off_axis_projection import off_axis_projection
import astropy.units as u
from astropy.coordinates import SkyCoord, CartesianRepresentation, concatenate
from astropy.wcs import WCS
import sunpy.map
from sunpy.coordinates import Heliocentric, HeliographicStonyhurst, Helioprojective
from sunpy.map.header_helper import make_fitswcs_header


class SyntheticImage:
    """Base class for handling simulation geometry and coordinate tracking"""

    def __init__(self, dataset, box_origin: SkyCoord, mm_per_unit: float = 2.4, **kwargs):
        self.ds = dataset
        self.box_origin = box_origin
        self.obstime = box_origin.obstime

        # Scaling factor: 2.4 Mm per grid unit is specific to the test simulation.
        # REVIEW: This factor should be derived from dataset metadata if possible.
        self.mm_per_unit = mm_per_unit
        self.box_dims = self.ds.domain_dimensions * u.Mm * self.mm_per_unit

        self.frame_hcc = Heliocentric(observer=self.box_origin, obstime=self.obstime)
        self.box_origin_hcc = self.box_origin.transform_to(self.frame_hcc)

        # box_origin marks the bottom (photospheric) boundary; box_center sits
        # half the vertical extent above it.
        self.box_center = SkyCoord(
            x=self.box_origin_hcc.x,
            y=self.box_origin_hcc.y,
            z=self.box_origin_hcc.z + self.box_dims[2] / 2,
            frame=self.box_origin_hcc.frame,
        )

        # Two parallel representations of the same 4 bottom-plane corners:
        #  - "ds" corners: dataset/code-unit coordinates, used for yt's
        #    off_axis_projection + coord_projection pixel-space math.
        #  - "sky" corners: real SkyCoords (offset from box_center using the
        #    physical box_dims), used for WCS registration against real data.
        self.bottom_corners_ds = self._generate_bottom_corners_ds()
        self.bottom_corners_sky = self._generate_bottom_corners_sky()

    def _generate_bottom_corners_ds(self):
        """4 corners of the bottom (z-min) plane in the dataset's native
        code-unit coordinates."""
        left = self.ds.domain_left_edge.v
        right = self.ds.domain_right_edge.v

        x_bounds = [left[0], right[0]]
        y_bounds = [left[1], right[1]]
        z_bottom = [left[2]]

        corners = list(itertools.product(x_bounds, y_bounds, z_bottom))
        return [unyt_array(list(pt), self.ds.domain_left_edge.units) for pt in corners]

    def _generate_bottom_corners_sky(self):
        """Same 4 corners as real SkyCoords, offset from box_center in
        physical Mm (using box_dims), mirroring the box-corner construction
        used to visualize the extrapolation cube against real imagery."""
        half_x = self.box_dims[0] / 2
        half_y = self.box_dims[1] / 2
        z_bottom = -self.box_dims[2] / 2  # bottom plane, relative to box_center

        coords = []
        for dx, dy in itertools.product([-half_x, half_x], [-half_y, half_y]):
            coords.append(SkyCoord(
                x=self.box_center.x + dx,
                y=self.box_center.y + dy,
                z=self.box_center.z + z_bottom,
                frame=self.box_center.frame,
            ))
        return coords

    def coord_projection(self, coord, orientation):
        """Reproduces yt's plot_modifications._project_coords: projects a
        3D dataset-frame point onto the 2D image plane defined by
        `orientation`."""
        coord_vectors = coord.transpose() - (self.ds.domain_center.v * self.ds.domain_center.uq)
        unit_vectors = orientation.unit_vectors
        x = np.dot(coord_vectors, unit_vectors[0]) + self.ds.domain_center.value[0]
        y = np.dot(coord_vectors, unit_vectors[1]) + self.ds.domain_center.value[1]
        return x, y


class SyntheticFilterImage(SyntheticImage):
    """Handles instrument-specific projection and WCS registration"""

    def __init__(self, dataset, box_origin, ref_map, resolution=512, **kwargs):
        super().__init__(dataset, box_origin, **kwargs)
        self.ref_map = ref_map
        self.resolution = resolution
        self.observer = ref_map.observer_coordinate

        # Calculate vectors for view alignment
        self.los_vec = self._get_los_vector()
        self.north_vec = self._get_north_vector()

        self.orientation = Orientation(self.los_vec, north_vector=self.north_vec)
        self.width = np.sqrt(2.) * self.ds.domain_width.max()

        # REVIEW: 'temperature' is a placeholder; the actual emissivity field
        # should be selected based on instrument/channel (cf. rushlight's
        # SyntheticImage, which picks a field per instr/channel pair).
        self.raw_image = off_axis_projection(
            self.ds, self.ds.domain_center, self.los_vec,
            self.width, self.resolution, ("gas", "temperature"),
        )

        self.synth_map = self.register_map()

    def _get_los_vector(self):
        """Line-of-sight unit vector from the box origin to the observer,
        in the box's Heliocentric frame."""
        obs_hcc = self.observer.transform_to(self.box_origin_hcc.frame)
        los = [obs_hcc.x - self.box_origin_hcc.x,
               obs_hcc.y - self.box_origin_hcc.y,
               obs_hcc.z - self.box_origin_hcc.z]
        los = np.array([comp.value for comp in los])
        return los / np.linalg.norm(los)

    def _get_north_vector(self):
        """Camera north unit vector, derived from the reference map's
        rotation matrix and mapped back into Heliographic Stonyhurst."""
        rot_matrix = self.ref_map.rotation_matrix
        cam_default = np.array([0, 1])
        cam_pt = np.dot(rot_matrix, cam_default)  # 2-element camera-pointing vector

        north_hcc = SkyCoord(
            CartesianRepresentation(cam_pt[0] * u.Mm, cam_pt[1] * u.Mm, 0 * u.Mm),
            obstime=self.obstime, observer=self.observer, frame="heliocentric",
        )
        north_cart = north_hcc.transform_to('heliographic_stonyhurst').cartesian
        north = np.array([north_cart.x.value, north_cart.y.value, north_cart.z.value])
        return north / np.linalg.norm(north)

    def _project_corners_to_pixels(self):
        """Projects each bottom-plane corner (dataset frame) to pixel
        coordinates on the rendered image, using the same geometry that
        produced self.raw_image."""
        pix_coords = []
        for pt3d in self.bottom_corners_ds:
            px_mm, py_mm = self.coord_projection(pt3d, self.orientation)
            px = (px_mm / self.width.value + 0.5) * self.resolution
            py = (py_mm / self.width.value + 0.5) * self.resolution
            pix_coords.append((px, py))
        return pix_coords

    def register_map(self):
        """Fits a WCS header by matching the projected pixel positions of
        the box's bottom corners to their true Helioprojective sky
        positions (using the full 4-corner spread for scale, as in the
        original notebooks), then wraps the rendered array in a sunpy Map."""

        pix_coords = self._project_corners_to_pixels()

        hpc_coords = concatenate(self.bottom_corners_sky).transform_to(
            Helioprojective(observer=self.observer, obstime=self.obstime)
        )

        pix_x = np.array([p[0] for p in pix_coords])
        pix_y = np.array([p[1] for p in pix_coords])

        width_arcsec = np.max(hpc_coords.Tx) - np.min(hpc_coords.Tx)
        height_arcsec = np.max(hpc_coords.Ty) - np.min(hpc_coords.Ty)
        width_pixels = np.max(pix_x) - np.min(pix_x)
        height_pixels = np.max(pix_y) - np.min(pix_y)

        cdelt1 = width_arcsec / width_pixels
        cdelt2 = height_arcsec / height_pixels

        ref_pixel = pix_coords[0]
        ref_coord = hpc_coords[0]

        header = make_fitswcs_header(
            data=self.raw_image.T,
            coordinate=ref_coord,
            reference_pixel=u.Quantity([ref_pixel[0], ref_pixel[1]] * u.pixel),
            scale=u.Quantity([cdelt1.value, cdelt2.value], unit=u.arcsec) / u.pix,
            observatory='Simulated',
        )
        return sunpy.map.Map((self.raw_image.T, header))