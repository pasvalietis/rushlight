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
            self.resolution = kwargs.get('resolution', 96)

            self.data = np.random.randint(0, 1e6, size=(self.resolution,
                                                   self.resolution))

            obstime = datetime.datetime(2000, 1, 1, 0, 0, 0)
            # Define a reference coordinate and create a header using sunpy.map.make_fitswcs_header
            skycoord_ = SkyCoord(0*u.arcsec, 0*u.arcsec, obstime=obstime,
                                observer='earth', frame=frames.Helioprojective)

            # Scale set to the following for solar limb to be in the field of view
            # Changes bounds of the resulting helioprojective view
            scale = kwargs.get('scale', 21)  # 21 arcsec/pix
            
            instr = kwargs.get('instr', 'DefaultInstrument')
            self.instr_default = 'DefaultInstrument'

            self.instrument = instr.lower()

            self.reference_pixel = ((self.resolution / 2.),
                                    (self.resolution / 2.)) * u.pix

            if 'channel' in kwargs:
                self.channel = kwargs['channel']
            if 'wavelength' in kwargs:
                self.wavelength = kwargs['wavelength']


            if self.instrument == 'xrt':

                header = make_fitswcs_header(self.data,
                                             coordinate=skycoord_,
                                             reference_pixel=self.reference_pixel,
                                             scale=[scale, scale]*u.arcsec/u.pixel,
                                             telescope=kwargs.get('telescope', self.instr_default),
                                             detector=kwargs.get('detector', self.instr_default),
                                             instrument=kwargs.get('instrument', self.instrument),
                                             observatory=kwargs.get('observatory', self.instr_default),
                                             wavelength=kwargs.get('wavelength', None),
                                             exposure=kwargs.get('exposure', None),
                                             unit=kwargs.get('unit', None),
                                             )

                header['EC_FW1_'] = 'Open'
                header['EC_FW2_'] = self.channel.replace("-", "_")  # e.g. 'Al_thick'

                default_kwargs = {'data': self.data, 'header': header}

                m = sunpy.map.Map(self.data, header)

            else:
                self.wavelength = self.channel  # Assuming channel contains EUV wavelength argument
                header = make_fitswcs_header(self.data,
                                             coordinate=skycoord_,
                                             reference_pixel=self.reference_pixel,
                                             scale=[scale, scale]*u.arcsec/u.pixel,
                                             telescope= kwargs.get('telescope', self.instr_default),
                                             detector= kwargs.get('detector', self.instr_default),
                                             instrument=kwargs.get('instrument', instr),
                                             observatory=kwargs.get('observatory', self.instr_default),
                                             wavelength= kwargs.get('wavelength', self.wavelength),
                                             exposure=kwargs.get('exposure', None),
                                             unit=kwargs.get('unit', None))


                default_kwargs = {'data': self.data, 'header': header}
                m = sunpy.map.Map(self.data, header)

        self.map = m

@dataclass
class XRTReferenceImage(ReferenceImage):
    """
    XRT instrument variant of default reference image object
    """

    def __init__(self, ref_img_path: str = None):
        super().__init__(ref_img_path, instrument='xrt')

@dataclass
class AIAReferenceImage(ReferenceImage):
    """
    AIA instrument variant of default reference image object
    """

    def __init__(self, ref_img_path):
        super().__init__(ref_img_path)