from flask import Flask, render_template, request, redirect, url_for
from socket import gethostname
from CountryCompare import CountryCompare as cc
import pandas as pd
import random as r
import datetime as dt
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
import cv2
import math

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
    global guessed_countries # will replace with proper cached list later
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
    todayscountrylat = float(locations.at[countries[country_index], 'latitude'])
    todayscountrylong = float(locations.at[countries[country_index], 'longitude'])

    # Process any guessed countries

    distance_compare_results = []
    guessed_distances = []
    guessed_directions = []
    guessed_image_result_path = []
    guessed_image_path = []
    guessed_directions_image_path = []

    for x in guessed_countries:
        guessedcountryid = locations.loc[locations['name'] == x, 'country'].values[0]
        guessedcountrylat = float(locations.loc[locations['name'] == x, 'latitude'].values[0])
        guessedcountrylong = float(locations.loc[locations['name'] == x, 'longitude'].values[0])

        guessed_path = 'src/static/images/cleaned_flags/' + str(guessedcountryid).lower() + '.png'
        answer_path = 'src/static/images/cleaned_flags/' + str(todayscountryid).lower() + '.png'

        image1 = cv2.imread(guessed_path)
        image2 = cv2.imread(answer_path)

        image_result = cc.match_colours(image1, image2)
        guessed_image_path.append(url_for('static', filename="/images/cleaned_flags/" + str(guessedcountryid).lower() + ".png"))
        guessed_image_result_path.append(url_for('static', filename="/guesses/output_" + str(guessedcountryid).lower() + ".png"))
        cv2.imwrite("src/static/guesses/output_" + str(guessedcountryid).lower() + ".png", image_result[1])

        coord1 = [guessedcountrylat, guessedcountrylong]
        coord2 = [todayscountrylat, todayscountrylong]

        

        

        distance_compare_results.append(cc.check_distance(coord1, coord2))

        guessed_distances = [sublist[0] for sublist in distance_compare_results]
        guessed_distances = [f"{int(round(x,0)/1000):,} km" if x != 0 else 0 for x in guessed_distances]
        guessed_directions = [sublist[3] for sublist in distance_compare_results]
        guessed_directions_image_path = [url_for('static', filename="/images/directions/" + sublist[3] + ".png") for sublist in distance_compare_results]



    # Zip the lists together before passing to the template
    guesses = zip(guessed_image_path, guessed_countries, guessed_distances, guessed_directions_image_path, guessed_image_result_path)
    
        

    return render_template("index.html"
                           , country = todayscountry
                           , countries = countries_sorted
                           , guesses = guesses)

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