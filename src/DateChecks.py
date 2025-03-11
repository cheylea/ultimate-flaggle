#!/usr/bin/python3
# Set of Python functions for comparing two flags

### Imports
import random as r
import datetime as dt
from datetime import date

### Functions related to date comparision to determine what country
### it is today and whether or not the user can still play today.

class DateChecks:
    # Function to check if we need to shuffle the list of countries
    def checkShuffle(last_shuffled_date, locations):
        """Check if out of a list if we need to reshuffle the list
        Returns a trust false for whether or not it needs to be
        reshuffled.

        Key arguments
        last_shuffled_date -- when the list was last shuffled
        locations -- list of items to shuffle
        """
        today = date.today()
        # If it has been 244 days since the last shuffle we shuffle again
        # This is to avoid cycling through the same order of countries over and over
        if last_shuffled_date > today + dt.timedelta(days=len(locations)):
            return 1
        else:
            return 0

    # Function to check if the player is viewing this on a new day
    def is_new_day(last_played):
        """Check if the last played date is different from today.
        
        Key arguments
        last_played -- when the user last played the game
        """
        today = dt.date.today().isoformat()
        return last_played != today