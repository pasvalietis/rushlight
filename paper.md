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

Part of rushlight's core motivation is to make EUV / SXR forward modelling more accessible to the growing company of astrophysicists who utilize the python language to develop and share scientific software. To this effect, rushlight has been developed as to be both compatible and scalable with release versions of other astrophysics open-source software, such as Astropy [@ASTROPY], SunPy [@SUNPY], and XRTpy [@XRTPY].

# Mathematics
Test

# Acknowledgements
Test

# References
Test
