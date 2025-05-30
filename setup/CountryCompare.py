#!/usr/bin/python3
# Set of Python functions for comparing two flags

### Imports
import numpy as np
from geographiclib.geodesic import Geodesic as geo
import cv2
import scipy.spatial as sp
from PIL import Image
import math
import numpy as np

class CountryCompare:
    # Function for cross references colours for two cleaned flags
    def match_colours(image1, image2):
        """Compare two flags and show the difference between them

        Key arguments
        image1 -- first image that uses cv2.imread on an image file
        image2 -- comparison image that uses cv2.imread on an image file
        """
        # Check if images are the same initially
        if image1.shape != image2.shape:
            match = True
        else:
            match = False

        # Compare images pixel by pixel and calculate the absolute difference between each pixel
        difference = np.subtract(image1, image2)
        abs_difference = np.abs(difference)
        abs_difference_sum = np.sum(abs_difference, axis=2)

        # Set a threshold of zero and create a mask for above and below the threshold
        threshold = 0
        mask_match = abs_difference_sum <= threshold
        mask_no_match = abs_difference_sum > threshold
        green = [0, 255, 0]
        black = [0, 0, 0]

        # Set matches to green and no matches to black
        difference[mask_no_match] = black
        difference[mask_match] = green
        
        # Calculate the percentage difference between the flags
        calc_match = np.sum(mask_match) / (np.sum(mask_match) + np.sum(mask_no_match)) * 100
        perc_match = "{:.2f}%".format(calc_match)

        # Return result
        return match, difference, perc_match
    
    def check_distance(coord1, coord2):
        """Compare two sets of lat-long coordinates and return the distance and direction between them
        Key arguments
        coord1 -- first set of coordinates eg. 42.546245,1.601554
        coord2 -- second set of coordinates to compare to, eg. 42.546245,1.601554
        """
        # Use geo to get the distance and bearing based on the latitude and longitude coordinates
        compare = geo.WGS84.Inverse(coord1[0], coord1[1], coord2[0], coord2[1])
        distance = compare['s12']
        curved_direction = compare['azi1']
        
        # Normalise the direction
        if curved_direction < 0:
            curved_direction += 360
        
        ### Change to rhumb line bearing
        # Calculate the rhumb line bearing (loxodrome)
        delta_lon = np.radians(coord2[1] - coord1[1])
        phi1 = np.radians(coord1[0])
        phi2 = np.radians(coord2[0])
        delta_psi = np.log(np.tan(np.pi / 4 + phi2 / 2) / np.tan(np.pi / 4 + phi1 / 2))
        rhumb_bearing = np.degrees(np.arctan2(delta_lon, delta_psi)) % 360
        direction = rhumb_bearing
        
        # Check if not making map sense
        lat_diff = coord2[0] - coord1[0]
        lon_diff = coord2[1] - coord1[1]
        if abs(lat_diff) > abs(lon_diff):  # More movement in latitude
            primary_direction = "north" if lat_diff > 0 else "south"
            #secondary_direction = "east" if lon_diff > 0 else "west"
        else:  # More movement in longitude
            primary_direction = "north" if lat_diff > 0 else "south"
            #secondary_direction = "east" if lon_diff > 0 else "west"
        
        # Handle cases where movement is mostly in one direction
        if direction > 0 and direction < 90 and primary_direction != "north":
            direction += 90
        # Handle cases where movement is mostly in one direction
        if direction > 270 and direction < 180 and primary_direction != "north":
            direction -= 90
        if direction > 90 and direction < 180 and primary_direction != "south":
            direction -= 90
        # Handle cases where movement is mostly in one direction
        if direction > 180 and direction < 270 and primary_direction != "south":
            direction += 90
        return direction, distance

    def process_flags(imagepath):
        """Change flag to specific colour palette

        Key arguments
        imagepath -- path for image to change
        """
        #reference: https://sethsara.medium.com/change-pixel-colors-of-an-image-to-nearest-solid-color-with-python-and-opencv-33f7d6e6e20d
        colours = [(0, 0, 0) # black 
                  ,(255, 255, 255) # white
                  ,(206, 36, 36) # dark red
                  ,(208, 16, 58) # red pink
                  ,(0, 121, 52) # green
                  ,(146, 22, 160) # purple
                  ,(15, 65, 163) # blue
                  ,(0, 175, 202) # bright blue
                  ,(140, 185, 218) # light blue
                  ,(222, 205, 182) # cream
                  ,(250, 243, 65) # yellow
                  ,(234, 203, 63) # gold
                  ,(255, 128, 0) # orange
                  ,(97, 54, 46) # brown
                  ,(160, 160, 160) # grey
                  ,(244, 142, 147) # pink
                  ] 
        
        image = cv2.imread(imagepath)
        # convert BGR to RGB image
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        h,w,bpp = np.shape(image)

        # Change colors of each pixel
        # reference :https://stackoverflow.com/a/48884514/9799700
        for py in range(0,h):
            for px in range(0,w):

              #Used this part to find nearest color 
              #reference : https://stackoverflow.com/a/22478139/9799700
              input_color = (image[py][px][0],image[py][px][1],image[py][px][2])
              tree = sp.KDTree(colours) 
              ditsance, result = tree.query(input_color) 
              nearest_color = colours[result]

              image[py][px][0]=nearest_color[0]
              image[py][px][1]=nearest_color[1]
              image[py][px][2]=nearest_color[2]
        
        image = Image.fromarray(image)
        image = image.resize((800,530))
        image.save(imagepath.replace("flags","cleaned_flags"))

