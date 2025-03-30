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
# example of close
coord1 = [53.825564,-2.421975] # uk
coord2 = [53.41291,-8.24389] # ireland

# example of normal direction pointing off map
coord1 = [64.963051,-19.020835] # iceland
coord2 = [27.514162,90.433601] # bhutan

# example of curve direction being very different to straight
coord1 = [36.204824,138.252924] # japan
coord2 = [21.512583,55.923255] # oman

result = cc.check_distance(coord1, coord2)

print(result)

