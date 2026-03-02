.. Rushlight documentation master file, created by
   sphinx-quickstart on Wed May 22 19:39:39 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Rushlight's documentation!
=====================================

Rushlight is a Python software module for solar physicists that generates synthetic observations from numerical simulation results.
It provides functionality to produce filter-band extreme ultraviolet (EUV) and soft X-ray images from user-defined line of sight.
Currently supported observatories include SDO (AIA instrument `[Lemen et al., 2010] <https://doi.org/10.1007/s11207-011-9776-8>`_) and Hinode (XRT instrument `[Golub et al., 2007] <https://doi.org/10.1007/978-0-387-88739-5_5>`_).


..
   Rushlight can be used to create synthetic observations and sunpy map objects compatible with the rest of the sunpy suite of functionality.

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: User Guide:

   install
   about

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Example notebooks:

   example_notebooks/eg_synth_proj

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: API Reference:

   rushlight.utils
   rushlight.emission_models

.. Check out the :doc:`usage` section for further information, including how to :ref:`install <installation>` the project.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
