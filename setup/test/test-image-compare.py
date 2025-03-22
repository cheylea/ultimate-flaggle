#!/usr/bin/python3
# Python program to compare two images of flags

# Imports
import sys
import os
import inspect

cdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(cdir)
sys.path.insert(0, parentdir)

import cv2
import numpy as np
from setup.CountryCompare import CountryCompare as cc

# Testing image comparison
image1 = cv2.imread('src/static/images/cleaned_flags/bd.png')
image2 = cv2.imread('src/static/images/cleaned_flags/sc.png')

result = cc.match_colours(image1, image2)

# Display the result
cv2.imwrite("output.png", result[1])


print(result[2])

# Testing flag processing
# imagepath = 'static/images/flags/ad.png'
# 
# cc.process_flags(imagepath)