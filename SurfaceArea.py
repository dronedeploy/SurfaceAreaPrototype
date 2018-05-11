import numpy as np
import rasterio as rs
import time, math, subprocess, json

def surface_area(DEM, resolution):
    """
    Compute surface area of DEM using sub-matrices
            1-----2-----3
            |\    |\    |
            |  \  |  \  |
            |    \|    \|
            4-----5-----6
            |\    |\    |
            |  \  |  \  |
            |    \|    \|
            7-----8-----9
    Consider the 9 elevation values shown above in a 3x3 DEM. We can estimate the surface area of the DEM by
    adding up the surface areas of 8 triangles they can compose. If we look at any set of 4 points:
                  m1
            1-----------2
            |  \        |
         m2 |    \m3    | m4
            |       \   |
            4-----------5
                 m5
    We can compute difference matrices m1, m2, m3, and m4 (the change in elevation between two points). The change in
    elevation calculation must also consider the horizontal distance, using resolution, as the second leg of
    Pythagoras' triangle:
                            |\
                            | \  <--- total length of DEM segment
       delta elevation -->  |  \
                            |___\
                              horizontal distance (from resolution)
    Then, the area for each triangle is computed using Heron's formula, which takes the 3 side lengths of a triangle
    https://en.wikipedia.org/wiki/Heron%27s_formula
    Finally, we use numpy to perform this operation on difference arrays, which is much more efficient than looping
    Args:
        DEM: Digital Elevation Model (numpy float array)
        resolution: DEM resolution, m/px
    Returns:
        Surface area of D, in m^2
    """

    resolution_squared = resolution ** 2.
    cross_distance_squared = 2.0 * (resolution ** 2.)

    m1 = ((DEM[0:-1, 0:-1] - DEM[0:-1, 1:]) ** 2.0 + resolution_squared) ** 0.5
    m2 = ((DEM[0:-1, 0:-1] - DEM[1:, 0:-1]) ** 2.0 + resolution_squared) ** 0.5
    m3 = ((DEM[0:-1, 0:-1] - DEM[1:, 1:]) ** 2.0 + cross_distance_squared) ** 0.5
    m4 = ((DEM[0:-1, 1:] - DEM[1:, 1:]) ** 2.0 + resolution_squared) ** 0.5
    m5 = ((DEM[1:, 0:-1] - DEM[1:, 1:]) ** 2.0 + resolution_squared) ** 0.5

    #from pdb import set_trace; set_trace()
    # Heron's formula for computing the area of a triangle, knowing 3 sides lengths,
    # requires a semiperimeter variable "s"
    s1 = 0.5 * (m3 + m5 + m2)
    s2 = 0.5 * (m3 + m4 + m1)

    # Calculate area using Heron's formula. This computes the upper and lower triangle area for each set of 4 dem points
    area = np.sum(np.sqrt(s1 * (s1 - m3) * (s1 - m5) * (s1 - m2))) + np.sum(np.sqrt(s2 * (s2 - m3) * (s2 - m4) * (s2 - m1)))

    return area

#Calculate the surface area from the Image
def getSurfaceAreaFromDEM(DEM, resolution):
    t0 = time.time()
    area = surface_area(DEM, resolution=resolution)
    t1 = time.time()
    print "Surface Area Approximation: %0.3f m^2  (took {%0.3f} s)" % (area, t1 - t0)

#Simple unit test of pyramid of elevation 1 and base length 2. Known reference surface area
def test_known_pyramid():
    D = np.array([[0, 0, 0],[0, 1, 0],[0, 0, 0]])
    getSurfaceAreaFromDEM(D,1.0)
    print "Expected Area: {:0.3f} m^2\n".format(4 * np.sqrt(2))

def compare_surface_area(filename, expected):
    dem_arr = rs.open(filename).read()
    json_data = subprocess.check_output(['rio','info',filename]) # '--indent','2'])
    dict_json = json.loads(json_data)
         
    #Extracting data from dictionary
    resolution = dict_json['res'][0]
    nodata = dict_json['nodata']

    #count_layer = dict_json['count']
    
    #Making sure the nodata don't get called during area calculations
    dem_arr[dem_arr==nodata] = 0.0

    #Calling the Surface area function
    getSurfaceAreaFromDEM(dem_arr[0], resolution)
    print "Expected Area Approximation: %s m^2\n" % (expected)

if __name__ == "__main__":

    #Testing with small array
    print("Test 1: Using a 3X3 array")
    test_known_pyramid()

    #Testing with two images
    print("Test 2: Using image")
    compare_surface_area('Test1.tif', '35.0')
    print("Test 3: Using image")
    compare_surface_area('Test2.tif', '2.52')

    """
    On the Dashboard,
    1. Go to elevation
    2. Go to crop feature
    3. Select the area required
    4. Export the map with: Layer=Elevation, File Type=Raw Elevation Values(DEM), Single Image and selecting appropriate resolution
    5. Download the exported file and make sure the .tif file is present

    Python Algorithm:
    6. Using rasterio, open the file in read mode.
    7. Using subprocess, get all the metadata of this image.
    8. Get the resolution and no data from this metadata [Note: 1) The metadata does have the coordinates (lat,long) 2) Can include checks here to make sure the file is in the right format and has single layer]
    Note: Tried using "get_mercator_resolution_from_zoom_and_lat()" from the URL's zoom level and latitude here but it resulted in inaccurate results. Used the rasterio's metadata resolution instead.
    9. Call the surface area function with the DEM matrix and resolution
    10. Compare it with the expected output (calculated manually)
                                                                                                                                                                     
    """

        