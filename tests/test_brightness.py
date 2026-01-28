import os, sys

import pytest
import pathlib
import tempfile
from pathlib import Path

import yt
import h5py
import numpy as np
import numpy.testing as npt

import rushlight
from rushlight.utils import dcube
from rushlight.utils.proj_imag_classified import SyntheticImage as sfi

import astropy.units as u


def test_imag_aia_131():

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, "test.h5")

        # Create a dummy dataset in the 'reference_data folder'
        dummy_ds = dcube.Dcube(output_file=temp_file_path)
        dataset = yt.load(temp_file_path)

        # Calculate synthetic image
        theta = 0.0
        norm_vec = [np.sin(np.radians(theta)), np.sin(np.radians(theta)), np.cos(np.radians(theta))]
        norm_one = 2 * (norm_vec / np.linalg.norm(norm_vec))

        sfiObj = sfi(dataset=dataset,
                     instr='AIA',
                     channel=131 * u.angstrom,
                     normvector=norm_one,
                     northvector=[0., 1., 0.])

        package_path = Path(rushlight.__file__)
        rlight_directory = package_path.parent
        repo_directory = rlight_directory.parent


        with h5py.File(repo_directory / "tests/reference_data/maps_gm.h5", "r") as ref_data:
            ref_group = ref_data['aia']['131']['0.0']

            # Compare generated synthetic image with one saved in the hdf5 file
            npt.assert_array_equal(
                sfiObj.synth_map.data,
                ref_group['0.0'][:],
            )

