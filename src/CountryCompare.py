#!/usr/bin/python3
# Python program to compare two images of flags

# Imports
import numpy as np
from geographiclib.geodesic import Geodesic as geo
import math

class CountryCompare:

    def match_colours(image1, image2):
        """Create a block to add to the chain

        Key arguments
        image1 -- first image that uses cv2.imread on an image file
        image1 -- comparison image that uses cv2.imread on an image file
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
        compare = geo.WGS84.Inverse(coord1[0], coord1[1], coord2[0], coord2[1])
        distance = compare['s12']
        bearing = compare['azi1']

        cardinals = ["north", "north east", "east", "south east", "south", "south west", "west", "north west"]
        bearing += 22.5
        bearing = bearing % 360
        bearing = int(bearing / 45) # values 0 to 7
        direction = cardinals [bearing]

        return distance, compare['azi1'], bearing, direction