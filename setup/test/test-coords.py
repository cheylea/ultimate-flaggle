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
from CountryCompare import CountryCompare as cc

# Testing image comparison

coord1 = [-4.038333,21.758664]
coord2 = [23.885942,45.079162] # bhutan

print(coord1)
result = cc.check_distance(coord1, coord2)

print(result)

