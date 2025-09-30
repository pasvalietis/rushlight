from abc import ABC
from dataclasses import dataclass

import numpy as np

import sunpy.map
from sunpy.map.header_helper import make_fitswcs_header
from sunpy.map.map_factory import MapFactory
from sunpy.coordinates import frames

from astropy.coordinates import SkyCoord
import astropy.units as u


@dataclass
class ReferenceImage(ABC, MapFactory):
    """
    Default object for reference image types
    """

    def __init__(self, ref_img_path: str = None, **kwargs):
        """Constructor for the default reference image object

        :param ref_img_path: Path to the reference image .fits file, defaults to None
        :type ref_img_path: str, optional
        """

        if ref_img_path:
            m = sunpy.map.Map(ref_img_path)
        else:
            import datetime

            # Create an empty dataset (entire solar disk)
            resolution = 2500
            # data = np.full((resolution, resolution), np.random.randint(100))
            data = np.random.randint(0, 1e6, size=(resolution, resolution))

            obstime = datetime.datetime(2000, 1, 1, 0, 0, 0)
            # Define a reference coordinate and create a header using sunpy.map.make_fitswcs_header
            skycoord = SkyCoord(0*u.arcsec, 0*u.arcsec, obstime=obstime,
                                observer='earth', frame=frames.Helioprojective)
            # Scale set to the following for solar limb to be in the field of view
            # scale = 220 # Changes bounds of the resulting helioprojective view
            scale = kwargs.get('scale', 1)
            
            instr = kwargs.get('instrument', 'DefaultInstrument')
            self.instrument = instr

            header_kwargs = {
                'scale': [scale, scale]*u.arcsec/u.pixel,
                'telescope': instr,
                'detector': instr,
                'instrument': instr,
                'observatory': instr,
                'exposure': 0.01 * u.s,
                'unit': u.Mm
            }

            header = make_fitswcs_header(data, skycoord, **header_kwargs)
            default_kwargs = {'data': data, 'header': header}
            m = sunpy.map.Map(data, header)

        self.map = m

@dataclass
class XRTReferenceImage(ReferenceImage):
    """
    XRT instrument variant of default reference image object
    """

    def __init__(self, ref_img_path: str = None):
        super().__init__(ref_img_path, instrument='Xrt')

@dataclass
class AIAReferenceImage(ReferenceImage):
    """
    AIA instrument variant of default reference image object
    """

    def __init__(self, ref_img_path):
        super().__init__(ref_img_path)