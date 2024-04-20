from flask import Flask, render_template
from socket import gethostname
from CountryCompare import CountryCompare as cc
import pandas as pd
import random as r
import datetime as dt
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, instance_relative_config=True)

# Functions used in app go here
def main():
    global locations
    global countries
    global lastshuffled

    # Get details about the locations
    locations = pd.read_csv('static\country latitude and longitude.csv')
    # Generate list of country indexes
    countries = list(range(0, 243)) #List out index to select "random" country
    # Start from today upon initialisation
    lastshuffled = date.today()
    

# Function to check if we need to shuffle
def checkShuffle(last_shuffled_date):
    today = date.today()
    if last_shuffled_date > today + dt.timedelta(days=244) or last_shuffled_date == today:
        return 1
    else:
        return 0


# ----- START

# Home page for website
@app.route("/")
def home():
    check_shuffle = checkShuffle(lastshuffled)

    if check_shuffle == 1:
        today = date.today()
        global countries
        countries = r.shuffle(countries)
        global lastshuffled
        lastshuffled = today
    
    country_index = abs((lastshuffled - today).days)
    country = countries[country_index]
    
    return render_template("index.html", country = check_shuffle)


# ----- END
if __name__ == '__main__':
    main()
    # If statement to prevent run when hosting in PythonAnywhere
    if 'liveconsole' not in gethostname():
        app.run() # app.run(debug=True, port = 8000) to set different port