How to selectively download a pair of AIA/SDO and EUVI/STEREO images
====================================================================

How to use Fido.search to collect a pair of time-correlated events using
a sunpy Fido query.

Let’s first import the relevant for the notebook.

.. code:: ipython3

    import aiastereo as aist
    
    from sunpy.net import Fido, attrs as a
    import astropy.units as u
    
    import os
    import sys

Let’s also define the paths and settings for this run. You can customize
the **FITS_DIR** and **FIDO_RESULTS** paths to select where your images
and search results are saved.

.. code:: ipython3

    # Local Paths (customizable)
    FITS_DIR = './observations/'        # Download folder for FITS images
    FIDO_RESULTS = './fido_results/'    # Download folder for summary of FIDO query
    
    # Settings for this run
    use_fido = True          # Boolean trigger for using Fido fetch
    stereo_a = True         # Selects stereo A data if true, and stereo B if false
    debug = True            # Bypasses user input by using default values for Fido fetch


Here, we define the start and end time for the fido search. The times
must be in the format ``####-##-##T##:##``. Type ``exit`` into the
**start_time** prompt to exit the loop.

.. code:: ipython3

    # Sets a time range
    while use_fido:
      try:
        if debug:
          start_time = "2012-07-19T10:00"
          end_time = "2012-07-19T11:00"
        else:
          # Prompt user for desired time range
          # Example: 2012-07-19T10:00, 2012-07-19T11:00
          start_time = aist.get_user_input("Enter the start time (eg. 2012-07-19T10:00): ")
          end_time = aist.get_user_input("Enter the end time (eg. 2012-07-19T11:00): ")
    
        # Convert user input to Fido.Time objects
        time = a.Time(start_time, end_time)
        break
      except:
        if start_time == 'exit': break
        print('Time range not valid. Try again!')


Let’s also define the target **wavelengths** for our images. The
wavelengths should be entered separated by commas, such as
``171, 195, 304``. Once again, type ``exit`` into the **wavelength**
prompt to exit the loop.

.. code:: ipython3

    # Sets the target wavelengths
    while use_fido:
      try:
        if debug:
          wavelengths = '171'
        else:
          # Prompt user to select desired AIA wavelengths (comma separated)
          wavelengths = aist.get_user_input("Enter comma-separated AIA wavelengths eg. 171, 195, 304 (Angstroms): ")
        
        wavs = [a.Wavelength(float(wav)*u.angstrom) for wav in wavelengths.split(",")]
        break
      except:
        if wavelengths == 'exit': break
        print('Wavelength selection not valid. Try again!')

Next, let’s use Fido to search for some correlated AIA / STEREO images
within the specified parameters. This cell will search for STEREO first
due to its limited time cadence, and then will search around available
timestamps for a comparable AIA image. For each specified wavelength, it
will save a summary of the query results to **FIDO_RESULTS**.

.. code:: ipython3

    # Search for one wavelength at a time to ensure match
    if use_fido:
      # Containers for later retrieval of results
      aia_results = []
      stereo_results = []
    
      for wav in wavs:
        print(f"Searching in {wav.max.value} band\n")
    
        aia_wav = wav
        stereo_wav = wav
    
        # If the wavelength is 195, search for 193 instead
        if stereo_wav == a.Wavelength(float(193)*u.angstrom):
          stereo_wav = a.Wavelength(float(195)*u.angstrom)
    
        # Search for STEREO data first
        src = 'STEREO_A' if stereo_a else 'STEREO_B'
        stereo_result = Fido.search(time, a.Instrument('SECCHI'), a.Source(src), a.Sample(1*u.minute), a.Physobs('Intensity'), stereo_wav)    
        n_stereo = stereo_result.__dict__['_numfile']
    
        n_aia = 0
        # If STEREO results are found, search for AIA data within that timeframe
        if n_stereo == 1:
          aia_result = aist.approx_stereo(stereo_result, aia_wav)
          n_aia = aia_result.__dict__['_numfile']
        elif n_stereo > 1:
          time = a.Time(stereo_result[0, 0]["Start Time"], stereo_result[-1, 0]["End Time"])
          aia_result = Fido.search(time, a.Instrument('AIA'), a.Sample(1*u.minute), a.Physobs('Intensity'), aia_wav)
          n_aia = aia_result.__dict__['_numfile']
          if n_aia == 0:
            n_aia = aia_result.__dict__['_numfile']
            aia_result = aist.approx_stereo(stereo_result, aia_wav)
        else:
          print("No STEREO results found in the specified timeframe.")
    
        print(f'{n_aia} AIA images found.')
    
        # Saves the results for next cell
        stereo_results.append(stereo_result)
        aia_results.append(aia_result)
    
        # Saves the results to local .txt file for easy viewing (notebook may truncate output)
        directory_path = FIDO_RESULTS
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        file = open(f'{directory_path}{start_time}_{end_time}_{wav.max.value}.txt', 'w')
        file.write(str(stereo_result))
        file.write(str(aia_result))
        file.close()
        


.. parsed-literal::

    Searching in 171.0 band
    
    No AIA in stereo range! 
    Attempting search in 10-minute window...
    
    20 AIA images found.


After executing the cell above, you can review the full list of entries
prepared for download at the **FIDO_RESULTS** path. Then, input the
index of the entry (``0,1,2,3...``) when promped in the following cell.
The selected entries will be downloaded to **FITS_DIR**.

.. code:: ipython3

    # Allows the user to select which searched event to download
    if use_fido:
      directory_path = FITS_DIR
      if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    
      for w, wav in enumerate(wavs):
          while True:
            try:
              if debug:
                aia_selection = '-1'
                stereo_selection = '-1'
              else:
                # Allow user to select results to download
                aia_selection = aist.get_user_input("Enter the index of the AIA result to download (or -1 to skip): ")
                stereo_selection = aist.get_user_input("Enter the index of the STEREO result to download (or -1 to skip): ")
    
              if int(aia_selection) > -1:
                aia_sel = aia_results[w][0, int(aia_selection)]
                download = Fido.fetch(aia_sel, path=FITS_DIR)
                print("Download errors (AIA):", download.errors)
    
              # Download selected STEREO data
              if int(stereo_selection) > -1:
                stereo_sel = stereo_results[w][0, int(stereo_selection)]
                download = Fido.fetch(stereo_sel, path=FITS_DIR)
                print("Download errors (STEREO):", download.errors)
    
              break
            except:
              if aia_selection == 'exit': sys.exit(1)
              print('Selection not valid. Try again!')


You can now continue to pairing and cropping your selected images in
`eg_aia_stereo_pair.ipynb <eg_aia_stereo_pair.ipynb>`__.
