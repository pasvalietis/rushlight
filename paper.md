---
title: 'rushlight - Python-based Forward Modelling of Coronal Plasma Models'
tags:
  - Python
  - visualization
  - solar
  - projection
  - modeling
authors:
  - name: Sabastian Fernandes
    orcid: 0009-0005-5227-5633
    corresponding: true
    equal-contrib: true
    affiliation: 1
  - name: Ivan Oparin
    orcid: 0000-0002-1876-1372
    equal-contrib: true
    affiliation: 1
affiliations:
 - name: Center For Solar-Terrestrial Research, New Jersey Institute of Technology, Newark, NJ 07102, USA
   index: 1
date: 2 December 2025
bibliography: paper.bib
---

# Summary
The rushlight Python package provides a framework for creating synthetic images of plasma structures for model-to-data comparisons with coronal events. It handles the projection and alignment of 3D simulated datasets to user-defined locations and orientations relative to the sun. The produced observables are comparable to observations made by instruments such as the Hinode X-Ray Telescope (XRT) and the Solar Dynamics Observatory Atmospheric Imaging Assembly (AIA). rushlight aims to integrate into the growing community of Python-based astrophysics software such as Astropy, SunPy and XRTpy.

# Statement of need
rushlight is a Python package which performs forward modelling of simulated 3D plasma datasets in the coronal environment. Its core functionality lies in creating synthetic observables in Soft X-Ray filter bands produced by XRT, and Ultraviolet / Extreme Ultraviolet filter bands produced by AIA.

rushlight adapts some of the core functionality of the FORWARD package, written in the Interactive Data Language (IDL) [@FORWARD]. It is under active development, and aims to be continually improved as to implement more of FORWARD's features.

Part of rushlight's core motivation is to make EUV / SXR forward modelling more accessible to the growing company of astrophysicists who utilize the python language to develop and share scientific software. To this effect, rushlight has been developed as to be both compatible and scalable with release versions of other astrophysics open-source software, such as Astropy [@ASTROPY1] [@ASTROPY2] [@ASTROPY3], SunPy [@SUNPY], and XRTpy [@XRTPY].

# Package Structure
rushlight's modules are organized as to promote the addition of new emission models and instruments to produce synthetic observables with. The package's main functionality comes from the following classes:

- `rushlight.utils.proj_imag_classified.SyntheticImage` - This module is the parent module to all other Synthetic Image classes, regardless of simulated filter type. It is responsible for translating user input into a single object containing both reference and model data. The Python module `yt` is used its ability to orient and project volumetric data from multiple simulation platforms. 
- `rushlight.utils.proj_imag_classified.SyntheticFilterImage` - rushlight is intended to be expanded upon by developing other modules similar to SyntheticFilterImage, which overloads the SyntheticImage class to apply the appropriate imaging models specific to UV and SXR observations. 
- `rushlight.utils.dcube.Dcube` - This module serves to process user provided simulation datasets into a `YTRegion` object. If one is not provided, it can generate a dummy uniform grid dataset.
- `rushlight.utils.rimage.ReferenceImage` - This module processes user provided reference observation maps into `sunpy.map.Map` objects from which coordinate data is later calculated.
- `rushlight.utils.synth_tools.calc_vect` - rushlight accepts user specification of 3 points in 3D space located on the intended projection plane for their simulation data. From these 3 points, it uses the simulated observer's location to calculate the vector that is normal to this plane, and the vector that determines the rotation of the projection relative to the normal axis. These `norm` and `north` vectors, respectively, are used in the yt.off_axis_projection module to calculate projection orientation.
- `rushlight.utils.emission_models.uv.UVModel` - This module is used by `rushlight.utils.proj_imag_classified.SyntheticFilterImage` to interpolate the temperature response function for a specified AIA channel, and then to utilize the density and temperature data from the simulation dataset to estimate the UV intensity of the solar plasma.
- `rushlight.utils.emission_models.xrt.XRTModel` - Similar to `rushlight.utils.emission_models.uv.UVModel`, this module instead interpolates the temperature response function for a specified combination of XRT filters to estimate the SXR intensity of the simulation dataset.

# Acknowledgements
Test

# References