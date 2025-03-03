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
from src.CountryCompare import CountryCompare as cc

# Testing image comparison

coord1 = [33.93911,67.709953]
coord2 = [-75.250973,-0.071389]

print(coord1)
result = cc.check_distance(coord1, coord2)

print(result)
