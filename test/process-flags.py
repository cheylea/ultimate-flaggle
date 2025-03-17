# Imports
import sys
import os
import inspect

cdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(cdir)
sys.path.insert(0, parentdir)

from src.CountryCompare import CountryCompare as cc
import pandas as pd

# Script used to loop through each flag to process it for comparing

# Get the list of the country codes
locations = pd.read_csv('src\static\country latitude and longitude.csv')

# Run through each country code
for x in range(0, len(locations)):
    imagepath = 'src/static/images/flags/FLAG.png'
    flag = locations.at[x, 'country']
    flag_path = imagepath.replace("FLAG",str(flag).lower()) # update image url to country code
    
    # Attempt to process the flag
    try:
        cc.process_flags(flag_path)
        print(str(x) + " complete.") # success
    except Exception as str_error:
        print(str(x) + " not there.") # fail
        pass