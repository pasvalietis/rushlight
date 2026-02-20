import os, sys

import pytest
import pathlib
import tempfile
from pathlib import Path

import yt
import h5py
import numpy as np
from numpy.testing import assert_allclose, assert_array_less, assert_raises

import rushlight
from rushlight.utils import dcube
from rushlight.utils.proj_imag_classified import SyntheticImage as sfi

import astropy.units as u
import atexit

temp_dir = tempfile.TemporaryDirectory()
TEMP_FILEPATH = os.path.join(temp_dir.name, "test.h5")

atexit.register(temp_dir.cleanup)

def gen_dummy_ds(temp_file_path):

    # Create a dummy dataset in the 'reference_data folder'
    dummy_ds = dcube.Dcube(output_file=temp_file_path)
    dataset = yt.load(temp_file_path)

    return dataset

temp_dataset = gen_dummy_ds(TEMP_FILEPATH)


def get_test_file_path():

    package_path = Path(rushlight.__file__)
    rlight_directory = package_path.parent
    repo_directory = rlight_directory.parent

    ref_file = repo_directory / "tests/reference_data/maps_gm.h5"

    return ref_file


def gen_test_synth_img():
    test_cases = {}
    ref_file = get_test_file_path()
    with h5py.File(ref_file, "r") as ref_data:
        instr_list = list(ref_data.keys())
        for instr in instr_list:
            channel_list = list(ref_data[instr].keys())
            for channel in channel_list:

                ref_group = ref_data[instr][channel]['0.0']
                args = ref_group['0.0'][:] # ref_data[group_name].attrs['my_args']

                path = f"{instr}/{channel}/{'0.0'}"

                test_name = f"{instr}-{channel}-{'0.0'}"

                params = [instr, channel, 0.0]

                test_cases[test_name] = (args, path)

    return test_cases

TEST_DICT = gen_test_synth_img()

@pytest.mark.parametrize(
    "args, dataset_path",
    list(TEST_DICT.values()),  # The actual data Pytest will use
    ids=list(TEST_DICT.keys()), # The names Pytest will print in the console!
)
def test_imag_face_on(args, dataset_path):
    """Test generation of synthetic images for all supported instruments/filters"""
    ref_file = get_test_file_path()
    instr, channel, theta_str = dataset_path.split('/')
    theta = float(theta_str)

    with h5py.File(ref_file, "r") as ref_data:
        expected_array = ref_data[dataset_path]['0.0'][:]

    #Calculate synthetic image
    norm_vec = [np.sin(np.radians(theta)), np.sin(np.radians(theta)), np.cos(np.radians(theta))]
    norm_one = (norm_vec / np.linalg.norm(norm_vec))

    if instr == 'aia': #'aia' in dataset_path:
        channel_ = int(channel) * u.angstrom
    else:
        channel_ = channel

    sfi_obj = sfi(dataset=temp_dataset,
                 instr=instr,
                 channel=channel_,
                 normvector=norm_one,
                 northvector=[0., 1., 0.])

    assert_allclose(
        sfi_obj.synth_map.data,
        expected_array,
        rtol = 1e-5,
        atol = 1e-8,
        err_msg=f"Synthetic image for {dataset_path} does not match expended standard",
    )
