from flask import Flask, render_template, request, redirect, url_for
from socket import gethostname
from CountryCompare import CountryCompare as cc
import pandas as pd
import random as r
import datetime as dt
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
import cv2

app = Flask(__name__, instance_relative_config=True)

# Functions used in the applications

def main():
    global locations
    global countries
    global lastshuffled
    global countries_sorted

    # Get details about the locations
    locations = pd.read_csv('src\static\country latitude and longitude.csv')
    # Generate list of country indexes
    countries = list(range(0, len(locations))) # List out index to select "random" country
    r.shuffle(countries)

    countries_sorted = sorted(locations['name'])

    # Start from today upon initialisation
    lastshuffled = date.today()

    global todayscountry
    global guessed_countries #will replace with proper cached list later
    guessed_countries = []
    

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
    global countries_sorted
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
    global todayscountry
    todayscountry = locations.at[countries[country_index], 'name']
    todayscountryid = locations.at[countries[country_index], 'country']
    todayscountrylat = locations.at[countries[country_index], 'latitude']
    todayscountrylong = locations.at[countries[country_index], 'longitude']

    # Process any guessed countries

    image_compare_results = []
    distance_compare_results = []
    for x in guessed_countries:
        guessedcountryid = locations.loc[locations['name'] == x, 'country']
        guessedcountrylat = locations.loc[locations['name'] == x, 'latitude']
        guessedcountrylong = locations.loc[locations['name'] == x, 'longitude']
        guessed_path = 'static/images/cleaned_flags/' + guessedcountryid + '.png'
        answer_path = 'static/images/cleaned_flags/' + todayscountryid + '.png'

        image1 = cv2.imread(guessed_path)
        image2 = cv2.imread(answer_path)

        coord1 = str(guessedcountrylat) + ',' + str(guessedcountrylong)
        coord2 = str(todayscountrylat) + ',' + str(todayscountrylong)

        image_compare_results.append(cc.match_colours(image1, image2))
        distance_compare_results.append(cc.check_distance(coord1, coord2))
    
    # then need to add a display for all the results in some way 



    return render_template("index.html", country = todayscountry, countries = countries_sorted, guessed_countries = guessed_countries)

# Compare Countries
@app.route("/guesscountry", methods=['GET', 'POST'])
def guesscountry():
    global guessed_countries
    guessed_country = request.form['guessedcountry']
    guessed_countries.append(guessed_country)

    return redirect("/")

# ----- END
if __name__ == '__main__':
    main()
    # If statement to prevent run when hosting in PythonAnywhere
    if 'liveconsole' not in gethostname():
        app.run() # app.run(debug=True, port = 8000) to set different port