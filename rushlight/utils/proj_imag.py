import os
import itertools
import numpy as np

import yt
from unyt import unyt_array
from yt.utilities.orientation import Orientation

import astropy.units as u
from astropy.coordinates import SkyCoord

from rushlight.emission_models import uv, xrt
from rushlight.utils.dcube import Dcube
from rushlight.utils import synth_tools as st

import sunpy.map
from sunpy.coordinates import Heliocentric, HeliographicStonyhurst, HeliographicCarrington, Helioprojective, get_earth

class SyntheticImage():

    def __init__(self,
                 dataset = None,
                 observer = None,
                 origin = SkyCoord(HeliographicStonyhurst(0.*u.deg, 0.*u.deg)),
                 resolution = 512,
                 smap=None,
                 **kwargs):

        self.ref_image = st.get_reference_image(smap, **kwargs)

        self.instr = kwargs.get('instr', None).lower()  # keywords: 'aia' or 'xrt'
        self.obs = kwargs.get('obs', "DefaultInstrument")  # Name of the observatory

        self.observer = observer if observer else self.ref_image.observer_coordinate
        self.obstime = kwargs.get('obstime', None)

        # Initialize the 3D MHD file to be used for synthetic image
        ds = Dcube(dataset)
        self.box = ds.box
        self.data = ds.data
        self.domain_width = ds.domain_width

        # Define origin point for model to data comparisons

        self.origin = origin

        self.normvector, self.northvector = (None, None)

        if 'normvector' in kwargs and 'northvector' in kwargs:
            self.normvector, self.northvector = kwargs['normvector'], kwargs['northvector']
        else:
            self.normvector, self.northvector = self.calculate_los_vector(self.observer, self.origin)

        # Define synth image attribute
        self.resolution = resolution
        self.image = None
    
    def derive_bottom_corner_coords(self, ds):
        """
        Function that defines coordinates for all corners of the dataset bottom plane in code units or Mm,
        and converts them to Heliocentric Cartesian frame to define 1 to 1 correspondence required for image registration
        """
        # Define the left and right edges of the dataset
        left = ds.domain_left_edge.v 
        right = ds.domain_right_edge.v

        # Define the values for each axis
        # We take both x limits, both y limits, but only the bottom z limit
        x_bounds = [left[0], right[0]]
        y_bounds = [left[1], right[1]]
        z_bottom = [left[2]]

        # x_bounds, y_bounds, z_bottom
        bottom_corners = list(itertools.product(x_bounds, y_bounds, z_bottom))



        bottom_coords_ds = ...
        bottom_coords_helioprojective = ...

        self.bottom_coords = {
            'bottom_coords_ds_frame': bottom_coords_ds,
            'bottom_coords_helioprojective': bottom_coords_helioprojective,
        }

    def calculate_los_vector(self, obs_location, origin_coord):
        """
        By default: load origin coord and define bottom plane aligned with cardinal directions (selected in helioprojective tangent plane)
        Optional: define bottom_coords manually; model will be aligned with these coordinates
        """
        
        # Get the box origin's Heliocentric Coordinates
        frame_hcc = Heliocentric(observer=origin_coord, obstime=origin_coord.obstime)
        origin_coord_hcc = origin_coord.transform_to(frame_hcc)

        # Get the observer's Heliocentric Coordinates
        observer_coord_hcc = obs_location.transform_to(origin_coord_hcc.frame)

        # Define the line of sight vector as the difference between box origin and observer
        los_vector = [
                     observer_coord_hcc.x - origin_coord_hcc.x,
                     observer_coord_hcc.y - origin_coord_hcc.y,
                     observer_coord_hcc.z - origin_coord_hcc.z,
                     ]
        
        los_vector = [comp.value for comp in los_vector] / np.linalg.norm([comp.value for comp in los_vector])
        
        # TODO: Properly account for observer's camera rotation
        north_vector = [0, 1, 0]

        return los_vector, north_vector

    def coord_projection(self, coord, dataset, orientation=None, **kwargs):
        """
        Reproduces yt plot_modifications _project_coords functionality
        """
        # coord_copy should be an unyt array in code_units
        coord_copy = coord
        coord_vectors = coord_copy.transpose() - (dataset.domain_center.v * dataset.domain_center.uq)

        # orientation object is computed from norm and north vectors
        if orientation:
            unit_vectors = orientation.unit_vectors
        else:
            if 'norm_vector' in kwargs:
                norm_vector = kwargs['norm_vector']
                norm_vec = unyt_array(norm_vector) * dataset.domain_center.uq
            if 'north_vector' in kwargs:
                north_vector = kwargs['north_vector']
                north_vec = unyt_array(north_vector) * dataset.domain_center.uq
            if 'north_vector' and 'norm_vector' in kwargs:
                orientation = Orientation(norm_vec, north_vector=north_vec)
                unit_vectors = orientation.unit_vectors

        y = np.dot(coord_vectors, unit_vectors[1]) + dataset.domain_center.value[1]
        x = np.dot(coord_vectors, unit_vectors[0]) + dataset.domain_center.value[0]  # * dataset.domain_center.uq

        ret_coord = (x, y)

        return ret_coord

    def return_pixel_coordinate(self, coord_2d_in_code_length, resolution, width):
        """
        Function to convert code coordinates of projected 2d points to pixel coordinates
        """

        pix_x = int((coord_2d_in_code_length[0] / width) * resolution) + int(resolution / 2)
        pix_y = int((coord_2d_in_code_length[1] / width) * resolution) + int(resolution / 2)

        return [pix_x, pix_y]


class SyntheticFilterImage(SyntheticImage):

    """
    Create synthetic filter image
    If the origin coordinate, observation time, and observer's location are provided,
    the image registration can be done
    """

    def __init__(self, dataset=None, smap_path: str=None, smap=None, **kwargs):
        super().__init__(dataset, smap_path, smap, **kwargs)

        self.proj_and_imag(**kwargs)
        self.make_synthetic_map(**kwargs)

    def make_filter_image_field(self):

        """Selects and applies the correct filter image field to the synthetic dataset

        :raises ValueError: Raised if filter instrument is unrecognized
        :raises ValueError: Raised if AIA wavelength is not from valid selection
                            (1600, 1700, 4500, 94, 131, 171, 193, 211, 304, 335)
        """

        cmap = {}
        imaging_model = None
        instr_list = ['xrt', 'aia', 'secchi', 'defaultinstrument']

        if self.instr not in instr_list:
            raise ValueError("instr should be in the instrument list: ", instr_list)

        if self.instr == 'xrt':
            imaging_model = xrt.XRTModel("temperature", "number_density", self.channel)
            cmap['xrt'] = cm.cmlist['hinodexrt']
        elif self.instr == 'aia':
            imaging_model = uv.UVModel("temperature", "number_density", self.channel)
            try:
                cmap['aia'] = cm.cmlist['sdoaia' + str(int(self.channel))]
            except ValueError:
                raise ValueError("AIA wavelength should be one of the following:"
                                 "1600, 1700, 4500, 94, 131, 171, 193, 211, 304, 335.")
        elif self.instr == 'secchi':
            self.instr = 'aia'  # Band-aid for lack of different UV model
            imaging_model = uv.UVModel("temperature", "number_density", self.channel)
            try:
                cmap['aia'] = cm.cmlist['sdoaia' + str(int(self.channel))]
            except ValueError:
                raise ValueError("AIA wavelength should be one of the following:"
                                 "1600, 1700, 4500, 94, 131, 171, 193, 211, 304, 335.")
        elif self.instr == 'defaultinstrument':
            print('DefaultInstrument used... Generating xrt intensity_field; self.instr = \'xrt\' \n')
            self.instr = 'xrt'
            imaging_model = xrt.XRTModel("temperature", "number_density", self.channel)
            cmap['xrt'] = cm.cmlist['hinodexrt']

        # Adds intensity fields to the self-contained dataset
        imaging_model.make_intensity_fields(self.data)

        field = str(self.instr) + '_filter_band'
        self.imag_field = field

        if self.plot_settings:
            self.plot_settings['cmap'] = cmap[self.instr]

    def proj_and_imag(self, **kwargs): # dataset, norm_vec, resolution, instr, **kwargs):
        """
        Function to compute projection of synthetic dataset using yt off_axis_projection module
        """

        self.make_filter_image_field()  # Create emission fields

        try:
            center = self.box.domain_center.value
        except:
            center = self.box.center

        imag_field = str(instr) + '_filter_band'

        prji = yt.off_axis_projection(
            self.box,
            center,  # center position in code units
            normal_vector=self.normvector,  # normal vector (z axis)
            width= np.sqrt(2.) * self.dataset.domain_width.max(),  # width in code units
            resolution=self.resolution,  # image resolution
            item=self.imag_field,  # respective field that is being projected
            north_vector= self.northvector,
            # depth = kwargs.get('depth', None)
        )

        self.image = np.array(prji).T

    def make_synthetic_map(self, **kwargs):
        """
        Creates a synthetic map object that can be loaded/edited with sunpy

        :return: Synthetic sunpy map created with projected dataset and specified header data
        :rtype: sunpy.map.Map
        """

        # Define header parameters for the synthetic image
        # Coordinates can be passed from sunpy maps that comparisons are made width

        self.reference_coord = self.ref_img.reference_coordinate
        self.reference_pixel = u.Quantity(self.ref_img.reference_pixel)

        asec2cm = _radius_from_angular_radius(1. * u.arcsec, 1 * u.AU).to(u.cm)  # centimeters per arcsecond at 1 AU
        resolution = self.plot_settings['resolution']
        domain_size = self.domain_width.max()
        len_asec = (domain_size / asec2cm).value
        scale_ = [len_asec / resolution, len_asec / resolution]

        self.scale = kwargs.get('scale', u.Quantity(self.ref_img.scale))
        self.telescope = kwargs.get('telescope', self.ref_img.detector)
        self.observatory = kwargs.get('observatory', self.ref_img.observatory)
        self.detector = kwargs.get('detector', self.ref_img.detector)
        self.instrument = kwargs.get('instrument', None)
        self.wavelength = kwargs.get('wavelength', self.ref_img.wavelength)
        self.exposure = kwargs.get('exposure', self.ref_img.exposure_time)
        self.unit = kwargs.get('unit', self.ref_img.unit)


        if self.instr.lower() == 'xrt':
            header = make_fitswcs_header(self.image,
                                         coordinate=self.reference_coord,
                                         reference_pixel=ref_pix,
                                         scale=self.scale,
                                         telescope=self.telescope,
                                         detector=self.detector,
                                         instrument=self.instrument,
                                         observatory=self.observatory,
                                         wavelength=self.wavelength,
                                         exposure=self.exposure,
                                         unit=self.unit,
                                         )

            # Determine Hinode/XRT filter wheel
            filter_wheel1_measurements = ["Al_med", "Al_poly", "Be_med",
                                          "Be_thin", "C_poly", "Open"]

            filter_wheel2_measurements = ["Open", "Al_mesh", "Al_thick",
                                          "Be_thick", "Gband", "Ti_poly"]

            if self.channel.replace("-", "_") in filter_wheel1_measurements:
                # Add support only for one filter in the filter wheel
                header['EC_FW1_'] = self.channel.replace("-", "_")
                header['EC_FW2_'] = 'Open'

            elif self.channel.replace("-", "_") in filter_wheel2_measurements:
                header['EC_FW1_'] = 'Open'
                header['EC_FW2_'] = self.channel.replace("-", "_")

            s_map = sunpy.map.Map(self.image, header)
            self.synth_map = sunpy.map.sources.XRTMap(s_map.data, s_map.fits_header)

            self.synth_map.plot_settings['norm'] = colors.LogNorm(self.ref_img.min(), self.ref_img.max())
            self.synth_map.plot_settings['cmap'] = self.plot_settings['cmap']

        else:
            header = make_fitswcs_header(self.image,
                                         coordinate=self.reference_coord,
                                         reference_pixel=ref_pix,
                                         scale=self.scale,
                                         telescope=self.telescope,
                                         detector=self.detector,
                                         instrument=self.instrument,
                                         observatory=self.observatory,
                                         wavelength=self.wavelength,
                                         exposure=self.exposure,
                                         unit=self.unit)

            self.synth_map = sunpy.map.Map(self.image, header)

            self.synth_map.plot_settings['norm'] = colors.LogNorm(self.ref_img.min(), self.ref_img.max())
            self.synth_map.plot_settings['cmap'] = self.plot_settings['cmap']

        return self.synth_map

    def register_smap(self):
        """
        Perform synthetic image registration using 2d projection of 3d points corresponding to bottom edge corners
        """

        bottom_corners_coords = self.bottom_coords['bottom_coords_ds_frame']
        bottom_corners = self.bottom_coords['bottom_coords_helioprojective']
