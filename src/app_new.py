#!/usr/bin/python3
# Ultimate Flaggle

###### I M P O R T S #####------------------------
import pandas as pd # for handling dataframes
import random as r
import datetime as dt
from datetime import date
import math
from socket import gethostname # for PythonAnywhere
from apscheduler.schedulers.background import BackgroundScheduler # for refreshing the page

# Setup Flask app
from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
app = Flask(__name__, instance_relative_config=True)

# Setup for identifying unique user id
import uuid

# Import custom functions
import cv2 # Required for using country compare
from CountryCompare import CountryCompare as cc # Import all functions from country compare
import sqlite3 # Required for using Database Functions
from DatabaseFunctions import DatabaseFunctions as sql # Import all SQLite connections functions
from DateChecks import DateChecks as dc # Import all functions for date comparison
#--------------------------------------------------

##### F U N C T I O N S #####----------------------
# 1. User UniqueId generation
# 2. Get the users game data
# 3. Main

# 1. User UniqueId generation 
def get_unique_id():
    """Get or create a unique ID for tracking."""
    unique_id = request.cookies.get("unique_id")
    if not unique_id:
        unique_id = str(uuid.uuid4())  # Generate a unique ID
    return unique_id

# 2. Get the users game data
def get_user_data(conn, unique_id):
    """Fetch user game data from the database.
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM GameDetail WHERE UniqueId = ? AND CAST(DateTimeGussed) = ?", (unique_id, date.today()))
    data = cursor.fetchone()

    conn.close()
    return data   

# 3. Main
# Function that runs upon initialisation.
def main():
    """Function that initialises the programme and sets
    up the starting databases

    """
    global locations
    global countries
    global lastshuffled
    global countries_sorted
    global max_guesses
    global country_index
    global conn
    
    max_guesses = 6

    # Create table for the flaggle game details database
    flaggle = r"databases\flaggle.db"
    conn = sql.connect_to_database(flaggle)

    # Answers
    drop_table_answer = """DROP TABLE IF EXISTS Answer; """
    create_table_answer = """ CREATE TABLE IF NOT EXISTS Answer (
                                CountryId text PRIMARY KEY,
                                Date date
                            ); """

    # Table that stores details of a persons game
    drop_table_games_detail = """DROP TABLE IF EXISTS GameDetail; """
    create_table_games_detail = """ CREATE TABLE IF NOT EXISTS GameDetail (
                                GameDetailId integer PRIMARY KEY,
                                UniqueId integer,
                                GameId integer,
                                DateTimeGuessed datetime,
                                GuessOrder integer,
                                CountryId, 
                                Distance float,
                                Direction text,
                                ComparedImageUrl text
                            ); """
    
    # Make connection to flaggle database file
    conn = sql.connect_to_database(flaggle)
    if conn is not None:
        # Execute required sql
        sql.execute_sql(conn, drop_table_answer)
        sql.execute_sql(conn, create_table_answer)
        sql.execute_sql(conn, drop_table_games_detail)
        sql.execute_sql(conn, create_table_games_detail)
        
        print("Database initialised.")
        
    else:
        print("Error, no connection.")

    
    # Get details about the locations
    locations = pd.read_csv('src\static\country latitude and longitude.csv')
    # Generate list of country indexes
    countries = list(range(0, len(locations))) # List out index to select "random" country
    r.shuffle(countries)
    countries_sorted = sorted(locations['name'])

    # Start shuffle from today upon initialisation
    lastshuffled = date.today()
    country_index = 0

#--------------------------------------------------


##### A P P L I C A T I O N #####------------------

# Home page for website
@app.route("/")
def home():
    global conn

    ### Set up the game and fetch any required user information
    global locations
    global lastshuffled
    global country_index
    today = date.today()
    # When page is loaded, checks if we need to reshuffle the list
    check_shuffle = dc.checkShuffle(lastshuffled, locations)
    # If we do, then shuffle the countries
    if check_shuffle == 1:
        r.shuffle(countries)
        lastshuffled = today
    # Systematically go through each index day by day to get todays country
    country_index = abs((lastshuffled - today).days)
    # Get todays' country
    todayscountry = locations.at[countries[country_index], 'name']
    todayscountryid = locations.at[countries[country_index], 'country']
    todayscountrylat = float(locations.at[countries[country_index], 'latitude'])
    todayscountrylong = float(locations.at[countries[country_index], 'longitude'])
    # Get any existing game data for the user
    user_id = get_unique_id()
    print(user_id)
    conn = sql.connect_to_database(r"databases\flaggle.db")
    
    
    ### Display any guessed countries for the user
    # Fetch game data
    game_data = get_user_data(conn, user_id)
    
    if game_data != None:
        #do some stuff where we get the existing to display 
        print("nothing here!...yet")
    
    return render_template("index.html", user_id = user_id, country = todayscountry, countries = countries_sorted)


# Compare Countries
@app.route("/guesscountry", methods=['GET', 'POST'])
def guesscountry(user_id, gameid):
    global conn
    global country_index

    # get user id and game id somehow

    guessed_country = request.form['guessedcountry']
    
    # Perform Country Compare Functions
    # Get values for the guessed country
    guessedcountryid = locations.loc[locations['name'] == guessed_country, 'country'].values[0]
    guessedcountrylat = float(locations.loc[locations['name'] == guessed_country, 'latitude'].values[0])
    guessedcountrylong = float(locations.loc[locations['name'] == guessed_country, 'longitude'].values[0])

    # Get values for todays country
    todayscountryid = locations.at[countries[country_index], 'country']
    todayscountrylat = float(locations.at[countries[country_index], 'latitude'])
    todayscountrylong = float(locations.at[countries[country_index], 'longitude'])

    # Calculate the distance and direction between the two countries
    coord1 = [guessedcountrylat, guessedcountrylong]
    coord2 = [todayscountrylat, todayscountrylong]

    distance_compare_result = cc.check_distance(coord1, coord2)

    guessed_distances = [sublist[0] for sublist in distance_compare_result]
    guessed_distances = [f"{int(round(x,0)/1000):,} km" if x != 0 else 0 for x in guessed_distances]
    guessed_directions = [sublist[3] for sublist in distance_compare_result]
    guessed_directions_image_path = [url_for('static', filename="/images/directions/" + sublist[3] + ".png") for sublist in distance_compare_result]

    # Retreive the urls for the cleaned flag images for both guesses and todays country
    guessed_path = 'src/static/images/cleaned_flags/' + str(guessedcountryid).lower() + '.png'
    answer_path = 'src/static/images/cleaned_flags/' + str(todayscountryid).lower() + '.png'
    image1 = cv2.imread(guessed_path)
    image2 = cv2.imread(answer_path)

    # Match colours and save resulting image
    image_result = cc.match_colours(image1, image2)
    cv2.imwrite("src/static/guesses/output_" + str(todayscountryid).lower() + "_" + str(guessedcountryid).lower() + ".png", image_result[1])
    guessed_image_path = "/images/cleaned_flags/" + str(guessedcountryid).lower() + ".png"
    guessed_image_result_path = "/guesses/output_" + str(todayscountryid).lower() + "_"  + str(guessedcountryid).lower() + ".png"


    # Store Results in Database

    # Insert block and used word into votes database
    try:
        insert_game_details = "INSERT INTO GameDetail (block) VALUES ('" + gameid + "', '" + dt.datetime.now() + "', '" + guessedcountryid + "', '" + distance + "', '" + direction + "', '" + image_url +");"
        insert_game = "INSERT INTO words (word, pollstation) VALUES ('" + secretword + "', '" + pollstation + "');"

        GameDetailId integer PRIMARY KEY,
        GameId integer,
        DateTimeGuessed datetime,
        GuessedCountryId, 
        Distance float,
        Direction text,
        ComparedImageUrl text

        sql.execute_sql(conn, insert_game_details)
        sql.execute_sql(conn, insert_game)
        conn.commit()
        conn.close
    except:
        return redirect("error.html")
    
    return redirect("/")

#--------------------------------------------------

##### I N I T I A L I S A T I O N #####
if __name__ == '__main__':
    main()
    # If statement to prevent run when hosting in PythonAnywhere
    if 'liveconsole' not in gethostname():
        app.run() # app.run(debug=True, port = 8000) to set different port

#--------------------------------------------------