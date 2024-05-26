from flask import Flask, render_template
from socket import gethostname
from CountryCompare import CountryCompare as cc
import pandas as pd
import random as r
import datetime as dt
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, instance_relative_config=True)

# Functions used in the applications

def main():
    global locations
    global countries
    global lastshuffled

    # Get details about the locations
    locations = pd.read_csv('static\country latitude and longitude.csv')
    # Generate list of country indexes
    countries = list(range(0, len(locations))) # List out index to select "random" country
    r.shuffle(countries)
    # Start from today upon initialisation
    lastshuffled = date.today()
    

# Function to check if we need to shuffle
def checkShuffle(last_shuffled_date):
    today = date.today()
    # If it has been 244 days since the last shuffle we shuffle again
    # This is to avoid cycling through the same order of countries over and over
    if last_shuffled_date > today + dt.timedelta(days=len(locations)):
        return 1
    else:
        return 0


# ----- START

# Home page for website
@app.route("/")
def home():
    global lastshuffled

    # When page is loaded, checks if we need to reshuffle the list
    check_shuffle = checkShuffle(lastshuffled)

    today = date.today()

    # If we do, then shuffle the countries
    if check_shuffle == 1:
        global countries
        r.shuffle(countries)
        lastshuffled = today
    
    # Systematically go through each index day by day
    country_index = abs((lastshuffled - today).days)

    # Get todays' country
    global locations
    country = locations.at[countries[country_index], 'name']
    
    return render_template("index.html", country = country)


# ----- END
if __name__ == '__main__':
    main()
    # If statement to prevent run when hosting in PythonAnywhere
    if 'liveconsole' not in gethostname():
        app.run() # app.run(debug=True, port = 8000) to set different port