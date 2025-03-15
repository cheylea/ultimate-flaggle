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
from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, session
app = Flask(__name__, instance_relative_config=True)
app.secret_key = "70656E6E79616E64626173696C" # Required for session

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
        # Create a response and set the cookie
        response = make_response(unique_id)
        response.set_cookie("unique_id", unique_id, max_age=60*60*24*365)  # Expires in 1 year
        return unique_id, response

    return unique_id, None  # If cookie exists, return the existing ID

# 2. Get the users game data from today
def get_user_game_data_today(conn, unique_id):
    """Fetch user game data from the database for today.
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("SELECT CountryId, Distance, Direction, ComparedImageUrl FROM GameDetail WHERE UniqueId = ? AND date(DateTimeGuessed) = ?", (unique_id, date.today()))
    data = cursor.fetchall()

    conn.close()
    return data

# 2. Get the users game data from today
def get_user_last_game_id(conn, unique_id):
    """Fetch the gameid last stored for the user
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(GameId) FROM GameDetail WHERE UniqueId = ?", (unique_id,))
    data = cursor.fetchone()

    conn.close()
    return data

# 2. Insert game guess
def insert_game_guess(conn, unique_id, game_id, country_id, distance, direction, image_url):
    """Insert the latest game guess
    
    Key arguments
    conn -- connection to the sqlite database
    unique_id -- unique id for a given user
    game_id -- the id for the game
    country_id -- an id code for a guesses country
    distance -- float value for distance between guessed country and answer
    direction -- value for direction between guessed country and answer
    image_url -- the image url for compared flags
    """
    cursor = conn.cursor()

    # Correct SQL query: specify all the column names
    sql = """
    INSERT INTO GameDetail (UniqueId, GameId, DateTimeGuessed, CountryId, Distance, Direction, ComparedImageUrl)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    cursor.execute(sql, (unique_id, game_id, dt.datetime.now(), country_id, distance, direction, image_url))
    conn.commit()
    cursor.close()

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
    global flaggle
    
    max_guesses = 6

    # Create table for the flaggle game details database
    flaggle = r"databases\flaggle.db"

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
    global flaggle
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
    # Get any existing id for user
    user_id, response = get_unique_id()
    
    
    
    ### Display any guessed countries for the user
    # Fetch todays game data
    conn = sql.connect_to_database(flaggle)
    user_today_data = get_user_game_data_today(conn, user_id)
    conn.close
    # Fetch id for last game played
    conn = sql.connect_to_database(flaggle)
    game_id = get_user_last_game_id(conn, user_id)
    conn.close
    game_id = game_id[0]
    # Generate new game id
    if game_id != None and user_today_data == []:
        game_id = game_id + 1 # Increase last game id by 1
        print("First guess of the day!")
    if game_id == None:
        game_id = 1 # First game for this user
        print("First game ever!")

    if user_today_data:
        print("nothing here!...yet")
        guessed_country_id, guessed_distances, direction, image_url = zip(*user_today_data)
    else:
        guessed_country_id, guessed_distances, direction, image_url = [], [], [], []  # Empty lists if no data

    # Format the select results to display in the template
    guessed_image_path = ["/static//images/cleaned_flags/" + str(x).lower() + ".png" for x in guessed_country_id]
    guessed_distances = [f"{int(round(x,0)/1000):,} km" if x != 0 else 0 for x in guessed_distances]
    guessed_directions_image_path = ["/static//images/directions/" + str(x).lower() + ".png" for x in direction]
    # Convert country IDs into Country Names
    country_name_dict = dict(zip(locations['country'], locations['name']))
    guesses_country_name = [country_name_dict.get(code, code) for code in guessed_country_id]

    # Check player game conditions
    if any(x == 0 for x in guessed_distances) == True:
        has_player_won = 1
    else:
        has_player_won = 0

    if len(guessed_country_id) == 6 and any(x == 0 for x in guessed_distances) != True:
        has_player_lost = 1
    else:
        has_player_lost = 0
    
    print(has_player_lost)
    print(has_player_won)

    # Zip the lists together before passing to the template
    guesses = zip(guessed_image_path, guesses_country_name, guessed_distances, guessed_directions_image_path, image_url)
    
    # Set session ids
    session["user_id"] = user_id
    session["game_id"] = game_id   

    
    # fix so it displays country name
    # maybe review the colour processing
    # need to add check for reaching 6 guesses and game over
    # need to add check for if the person has won and displaying the win + calculating the streak + guess statistics
    # that plus making the website just look better in general

    # Render the template normally
    rendered_template = render_template("index.html"
                           , country = todayscountry
                           , countries = countries_sorted
                           , guesses = guesses
                           , won = has_player_won
                           , lost = has_player_lost)

    if response:  
        # Set the response body to the rendered template
        response.set_data(rendered_template)
        return response  # Return response with cookie set

    return rendered_template  # If no new cookie, return the page normally

# Compare Countries
@app.route("/guesscountry", methods=['GET', 'POST'])
def guesscountry():
    global conn
    global country_index

    # Get user id and game id
    
    user_id = session.get("user_id")  # Retrieve the ID from query parameters
    game_id = session.get("game_id")  # Retrieve the ID from query parameters

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

    distance = distance_compare_result[0]
    direction = distance_compare_result[3]

    # Retreive the urls for the cleaned flag images for both guesses and todays country
    guessed_path = 'src/static/images/cleaned_flags/' + str(guessedcountryid).lower() + '.png'
    answer_path = 'src/static/images/cleaned_flags/' + str(todayscountryid).lower() + '.png'
    image1 = cv2.imread(guessed_path)
    image2 = cv2.imread(answer_path)

    # Match colours and save resulting image
    image_result = cc.match_colours(image1, image2)
    cv2.imwrite("src/static/guesses/output_" + str(todayscountryid).lower() + "_" + str(guessedcountryid).lower() + ".png", image_result[1])
    guessed_image_result_path = "/static//guesses/output_" + str(todayscountryid).lower() + "_"  + str(guessedcountryid).lower() + ".png"

    
    # Store Results in Database
    try:
        conn = sql.connect_to_database(flaggle)
        insert_game_guess(conn, user_id, game_id, guessedcountryid, distance, direction, guessed_image_result_path)
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