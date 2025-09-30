How to create a dummy volume
============================

This script demonstrates the process of creating a custom 3D dataset for
testing and visualization using the rushlight package.

- **NumPy Array Generation**: A 3D array is created with varying values
  along one axis and includes “cut-out” sections for visual interest.
- **yt Dataset Creation**: The NumPy array is loaded into a yt uniform
  grid dataset, with specified units and bounding box.
- **Data Export**: The created yt dataset is saved to an HDF5 file
  (``test.h5``).
- **Data Loading and Visualization**: The HDF5 file is then loaded back
  into a yt dataset, and ``yt_idv`` is used to render an interactive 3D
  visualization of the data.

.. code:: ipython3

    import yt
    import yt_idv
    
    import numpy as np

.. code:: ipython3

    # Create a generic NumPy dataset for demonstration purposes.
    
    # Define scaling factor for dimensions.
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
    
    # Cut out some chunks from the array to create a more visually distinctive dataset.
    # These chunks are set to the maximum value in `arr_range`.
    arr[dim0 - ch0 : dim0, dim1 - ch1 : dim1, dim2 - ch2 : dim2] = arr_range.max()
    arr[0:ch0, 0:ch1, 0:ch2] = arr_range.max()
    
    # Rotate the array to reorient the data.
    arr = np.rot90(arr, k=-1, axes=(0, 1))
    arr = np.rot90(arr, k=1, axes=(0, 2))


.. code:: ipython3

    # Create a yt object from the NumPy array.
    
    T_arr = arr  # Assign the generated array to represent temperature.
    D_arr = arr * 2  # Create a density array by scaling the temperature array.
    
    # Define the data dictionary with field names, arrays, and their units.
    # Units can be specified using CGS (centimeter-gram-second) units.
    data = {
        "temperature": (T_arr, "K"),
        "density": (D_arr, "g/cm**3"),
    }
    
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
    fn = cg.save_as_dataset(filename="test.h5", fields=[("gas", "temperature"), ("stream", "density")])



.. parsed-literal::

    yt : [INFO     ] 2025-08-04 10:04:11,956 Parameters: current_time              = 0.0
    yt : [INFO     ] 2025-08-04 10:04:11,957 Parameters: domain_dimensions         = [ 96 193 192]
    yt : [INFO     ] 2025-08-04 10:04:11,959 Parameters: domain_left_edge          = [-0.5   0.   -0.25]
    yt : [INFO     ] 2025-08-04 10:04:11,961 Parameters: domain_right_edge         = [0.5  1.   0.25]
    yt : [INFO     ] 2025-08-04 10:04:11,963 Parameters: cosmological_simulation   = 0
    yt : [INFO     ] 2025-08-04 10:04:13,081 Saving field data to yt dataset: test.h5.


.. code:: ipython3

    # Load the generic data object from the generated .h5 file.
    ds = yt.load("test.h5")



.. parsed-literal::

    yt : [INFO     ] 2025-08-04 10:04:13,687 Parameters: current_time              = 0.0 code_time
    yt : [INFO     ] 2025-08-04 10:04:13,688 Parameters: domain_dimensions         = [ 96 193 192] dimensionless
    yt : [INFO     ] 2025-08-04 10:04:13,689 Parameters: domain_left_edge          = [-0.5   0.   -0.25] code_length
    yt : [INFO     ] 2025-08-04 10:04:13,689 Parameters: domain_right_edge         = [0.5  1.   0.25] code_length
    yt : [INFO     ] 2025-08-04 10:04:13,690 Parameters: cosmological_simulation   = 0


.. code:: ipython3

    # Visualize the yt object using yt_idv.
    
    win_dim = 900  # Define the window dimension for visualization.
    
    # Create a render context for interactive 3D visualization.
    # `height` and `width` set the window size, `gui=True` enables the GUI.
    rc = yt_idv.render_context(height=win_dim, width=win_dim, gui=True)
    
    # Add a scene to the render context.
    # The dataset `ds` and the field `('gas', 'temperature')` are specified.
    # `no_ghost=True` prevents the rendering of ghost zones.
    sg = rc.add_scene(ds, ("gas", "temperature"), no_ghost=True)
    
    # Run the render context to display the visualization.
    rc.run()


.. parsed-literal::

    Setting position 510.0 90.0
    Computed new cmap values 4.78321771879564e-06 - 1.0

