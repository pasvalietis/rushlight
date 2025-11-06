from abc import ABC
from dataclasses import dataclass

import numpy as np

import yt
from yt.data_objects.selection_objects.region import YTRegion
yt.set_log_level(50)

@dataclass
class Dcube(ABC):

    def __init__(self, dataset = None):

        if not dataset:
            # Default values for bbox dimensions (code units)
            fract = 1
            dim0 = int(193 / fract)
            dim1 = int(192 / fract)
            dim2 = int(96 / fract)

            # Store dimensions in a list. Example: [depth, height, width].
            dims = [dim0, dim1, dim2]

            # Define the range for the logarithmic distribution.
            mi = 4
            ma = 8

            # Create a logarithmically spaced array based on the first dimension in 'dims'.
            arr_range = np.logspace(mi, ma, dims[0])

            # Initialize an empty array with the specified arbitrary dimensions.
            arr = np.empty(tuple(dims))

            # Fill the array. The 'fill' value varies along the first dimension (axis 0).
            # The `np.full` call creates a 2D array that matches the remaining dimensions
            # (dims[1] and dims[2]).
            for i in range(0, dims[0]):
                fill = arr_range[i]
                arr[i] = np.full((dims[1], dims[2]), fill)

            # Define scaling factor for creating "chunks" in the dataset.
            fract = 3
            ch0 = int(dims[0] / fract)
            ch1 = int(dims[1] / fract)
            ch2 = int(dims[2] / fract)

            max_val = arr_range.max()*1000

            # Cut out some chunks from the array to create a more visually distinctive dataset.
            # These chunks are set to the maximum value in `arr_range`.
            arr[dim0 - ch0 : dim0, dim1 - ch1 : dim1, dim2 - ch2 : dim2] = max_val
            arr[0:ch0, 0:ch1, 0:ch2] = max_val

            # Define the border thickness
            border_size = 1

            # 1. Edges along Dimension 0 (Front and Back planes)

            # Front-face-adjacent volume (spanning 0 to border_size along dim 0)
            arr[:border_size, :border_size, :] = max_val                    # Top border volume (along dim 1)
            arr[:border_size, -border_size:, :] = max_val                   # Bottom border volume (along dim 1)
            arr[:border_size, border_size:-border_size, :border_size] = max_val # Left border volume (along dim 2, excluding corners)
            arr[:border_size, border_size:-border_size, -border_size:] = max_val # Right border volume (along dim 2, excluding corners)

            # Back-face-adjacent volume (spanning dims[0]-border_size to end along dim 0)
            arr[-border_size:, :border_size, :] = max_val                   # Top border volume (along dim 1)
            arr[-border_size:, -border_size:, :] = max_val                  # Bottom border volume (along dim 1)
            arr[-border_size:, border_size:-border_size, :border_size] = max_val # Left border volume (along dim 2)
            arr[-border_size:, border_size:-border_size, -border_size:] = max_val # Right border volume (along dim 2)

            # 2. Edges along Dimension 1 (Top and Bottom planes)

            # Top-face-adjacent volume (spanning 0 to border_size along dim 1)
            arr[:border_size, :border_size, :] = max_val                    # Front border volume (along dim 0)
            arr[-border_size:, :border_size, :] = max_val                   # Back border volume (along dim 0)
            arr[border_size:-border_size, :border_size, :border_size] = max_val # Left border volume (along dim 2, excluding corners)
            arr[border_size:-border_size, :border_size, -border_size:] = max_val # Right border volume (along dim 2, excluding corners)

            # Bottom-face-adjacent volume (spanning dims[1]-border_size to end along dim 1)
            arr[:border_size, -border_size:, :] = max_val                   # Front border volume (along dim 0)
            arr[-border_size:, -border_size:, :] = max_val                  # Back border volume (along dim 0)
            arr[border_size:-border_size, -border_size:, :border_size] = max_val # Left border volume (along dim 2)
            arr[border_size:-border_size, -border_size:, -border_size:] = max_val # Right border volume (along dim 2)

            # 3. Edges along Dimension 2 (Left and Right planes)

            # Left-face-adjacent volume (spanning 0 to border_size along dim 2)
            arr[:border_size, :, :border_size] = max_val                    # Front border volume (along dim 0)
            arr[-border_size:, :, :border_size] = max_val                   # Back border volume (along dim 0)
            arr[border_size:-border_size, :border_size, :border_size] = max_val # Top border volume (along dim 1, excluding corners)
            arr[border_size:-border_size, -border_size:, :border_size] = max_val # Bottom border volume (along dim 1, excluding corners)

            # Right-face-adjacent volume (spanning dims[2]-border_size to end along dim 2)
            arr[:border_size, :, -border_size:] = max_val                   # Front border volume (along dim 0)
            arr[-border_size:, :, -border_size:] = max_val                  # Back border volume (along dim 0)
            arr[border_size:-border_size, :border_size, -border_size:] = max_val # Top border volume (along dim 1)
            arr[border_size:-border_size, -border_size:, -border_size:] = max_val # Bottom border volume (along dim 1)
            
            # Rotate the array to reorient the data
            arr = np.rot90(arr, k=-1, axes=(0, 1))
            arr = np.rot90(arr, k=1, axes=(0, 2))

            # %%
            # Create a yt object from the NumPy array.

            T_arr = arr * 1e-4        # Assign the generated array to represent temperature.
            D_arr = arr * 2e-22     # Create a density array by scaling the temperature array.

            # Define the data dictionary with field names, arrays, and their units.
            # Units can be specified using CGS (centimeter-gram-second) units.
            data = {
                "temperature": (T_arr, "K"),
                "density": (D_arr, "g/cm**3"),
            }

            # NOTE - change this to be symmetric
            # Define the spatial ranges for the bounding box.
            xrange = np.array([-0.5, 0.5])  # Length = 1 unit.
            yrange = np.array([0, 1])  # Length = 1 unit.
            zrange = np.array([-0.25, 0.25])  # Length = 0.5 units.

            # Combine ranges to form the bounding box.
            bbox = np.array([xrange, yrange, zrange])

            # Load the uniform grid data into a yt dataset object.
            # The unit length (1.5e10 cm = 1.5e5 km) is specified.
            ds = yt.load_uniform_grid(
                data,
                arr.shape,
                1.5e10,  # 1.5e10 cm = 1.5e5 km (unit length)
                bbox=bbox,
            )

            # Create a covering grid from the dataset at level 0.
            cg = ds.covering_grid(
                level=0,
                left_edge=[xrange[0], yrange[0], zrange[0]],
                dims=ds.domain_dimensions,
            )

            # Save the covering grid as an HDF5 dataset.
            # The `fields` argument specifies the fields to be saved.
            fname = "test.h5"
            fn = cg.save_as_dataset(filename=fname, fields=[("gas", "temperature"), ("stream", "density")])
            print('Saved dummy dataset to: ' + fname)

            dataset = yt.load("test.h5")
        
        if isinstance(dataset, YTRegion):
            self.box = dataset
            self.data = self.box.ds
            self.domain_width = np.abs(self.box.right_edge - self.box.left_edge).in_units('cm').to_astropy() #TODO generalize this cm parameter
        else:
            if isinstance(dataset, str):
                self.data = yt.load(dataset)
                self.box = self.data
            else:
                try:
                    dataset.field_list
                    self.data = dataset
                    self.box = self.data
                except:
                    raise("Datacube loading failed - please check for available fields: box")
            self.domain_width = np.abs(self.data.domain_right_edge - self.data.domain_left_edge).in_units('cm').to_astropy()
