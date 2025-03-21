#!/usr/bin/python3
# Ultimate Flaggle

###### I M P O R T S #####------------------------
import os
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

# Setup for identifying unique user id and using cookies
import uuid

# Import custom functions
import cv2 # Required for using country compare

# Import all functions from country compare
import numpy as np
from geographiclib.geodesic import Geodesic as geo
import cv2
import scipy.spatial as sp
from PIL import Image

# Required for using Database Functions
import sqlite3

# Set paths
from pathlib import Path
THIS_FOLDER = Path(__file__).parent.resolve()
#--------------------------------------------------


##### F U N C T I O N S #####----------------------
# 1.  User UniqueId generation
# 2.  Get the users game data
# 3.  Get the users last game id
# 4.  Insert game guess
# 5.  Get the users total guess counts over time
# 6.  Get the average guesses on winning games for a user
# 7.  Get the average time to win for a user
# 8.  Get the users current win streak
# 9.  Get the user's max win streak
# 10. Get the win rate
# 11. Get the total number of games played
# 12. Get values for the one screen stats chart
# 13. Get all of a users stats
# 14. Main

# 1. User UniqueId generation 
def get_unique_id():
    """Get or create a unique ID for tracking depending on cookie consent."""
    unique_id = request.cookies.get("unique_id")
    consent_status = check_consent()

    # Generate a unique_id if there isn't one
    if unique_id is None:
        unique_id = str(uuid.uuid4())

    # Set cookie if allowed
    if consent_status is True:
        # Create a response and set the cookie
        response = make_response(unique_id)
        response.set_cookie("unique_id", unique_id)
        return unique_id, response
    
    return unique_id, None  # If already cookie exists, return the existing ID

# 2. Get the users game data from today
def get_user_game_data_today(conn, unique_id):
    """Fetch user game data from the database for today.
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("SELECT CountryId, Distance, Direction, ComparedImageUrl FROM GameDetail WHERE UniqueId = ? AND date(DateTimeGuessed) = ? ORDER BY DateTimeGuessed DESC", (unique_id, date.today()))
    data = cursor.fetchall()

    conn.close()
    return data

# 3. Get the users last game id
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

# 4. Insert game guess
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

# 5. Get the users total guess counts over time
def get_player_guess_stats(conn, unique_id):
    """Get the users guess stats of all time
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("""SELECT 
                        UniqueId, 
                        TotalGuesses, 
                        COUNT(*) TotalGameCount 
                    FROM 
                    ( 
                        SELECT 
                            UniqueId, 
                            GameId, 
                            COUNT(*) AS TotalGuesses 
                        FROM GameDetail 
                        GROUP BY UniqueId, GameId 
                        HAVING MIN(Distance) = 0 
                    ) 
                    WHERE UniqueId = ?""", (unique_id,))
    data = cursor.fetchall()

    conn.close()
    return data

# 6. Get the average guesses on winning games for a user
def get_player_average_guess_stats(conn, unique_id):
    """Get the users average number of gueeses
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("""SELECT 
                        AVG(TotalGuesses) AS AverageGuesses
                    FROM
                    (
                        SELECT
                            UniqueId,
                            GameId,
                            COUNT(*) AS TotalGuesses
                        FROM GameDetail
                        GROUP BY UniqueId, GameId
                    )
                    WHERE UniqueId = ?
                    GROUP BY UniqueId""", (unique_id,))
                   
    data = cursor.fetchone()

    conn.close()
    return data[0] if data else 0

# 7. Get the average time to win for a user
def get_player_average_win_time(conn, unique_id):
    """Get the users average time in minutes to win a game
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("""SELECT 
                        ROUND(AVG(TimeTakenToFinishInMinutes),2) AS AverageWinTimeInMinutes
                    FROM
                    (
                        SELECT
                            UniqueId,
                            GameId,
                            MIN(DateTimeGuessed) AS StartTime,
                            MAX(DateTimeGuessed) AS EndTime,
                            (JULIANDAY(MAX(DateTimeGuessed)) - JULIANDAY(MIN(DateTimeGuessed))) * 24 * 60 AS TimeTakenToFinishInMinutes
                        FROM GameDetail
                        GROUP BY UniqueId, GameId
                        HAVING MIN(Distance) = 0
                    )
                    WHERE UniqueId = ?
                    GROUP BY UniqueId""", (unique_id,))
    data = cursor.fetchone()

    conn.close()
    return data[0] if data else 0

# 8. Get the users current win streak
def get_current_streak(conn, unique_id):
    """Get the user's current win streak.
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("""
        WITH WinningGames AS (
            SELECT 
                UniqueId,
                GameId,
                MIN(Distance) AS ClosestDistance,
                MIN(DATE(DateTimeGuessed)) AS DayPlayed
            FROM GameDetail
            GROUP BY UniqueId, GameId
            HAVING MIN(Distance) = 0
        ),
        RankedGames AS (
            SELECT 
                UniqueId,
                GameId,
                DayPlayed,
                ROW_NUMBER() OVER (PARTITION BY UniqueId ORDER BY DayPlayed) 
                - CAST(JULIANDAY(DayPlayed) AS INTEGER) AS StreakGroup 
            FROM WinningGames
        ),
        StreakCounts AS (
            SELECT 
                UniqueId,
                StreakGroup,
                COUNT(*) AS StreakLength,
                MAX(DayPlayed) AS LastWinDate
            FROM RankedGames
            GROUP BY UniqueId, StreakGroup
        ),
        CurrentStreak AS (
            SELECT 
                s.UniqueId, 
                s.StreakLength AS CurrentWinStreak
            FROM StreakCounts s
            JOIN (
                SELECT UniqueId, MAX(LastWinDate) AS LatestWin
                FROM StreakCounts
                GROUP BY UniqueId
            ) latest ON s.UniqueId = latest.UniqueId AND s.LastWinDate = latest.LatestWin
        )
        SELECT CurrentWinStreak FROM CurrentStreak
        WHERE UniqueId = ?;
    """, (unique_id,))

    data = cursor.fetchone()
    conn.close()

    return data[0] if data else 0  # Return 0 if no streak found

# 9. Get the user's max win streak
def get_max_streak(conn, unique_id):
    """Get the user's max win streak.
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("""
        WITH WinningGames AS (
            SELECT 
                UniqueId,
                GameId,
                MIN(Distance) AS ClosestDistance,
                MIN(DATE(DateTimeGuessed)) AS DayPlayed
            FROM GameDetail
            GROUP BY UniqueId, GameId
            HAVING MIN(Distance) = 0 -- Only winning games
        ),
        RankedGames AS (
            SELECT 
                UniqueId,
                GameId,
                DayPlayed,
                ROW_NUMBER() OVER (PARTITION BY UniqueId ORDER BY DayPlayed) 
                - JULIANDAY(DayPlayed) AS StreakGroup
            FROM WinningGames
        ),
        StreakCounts AS (
            SELECT 
                UniqueId,
                StreakGroup,
                COUNT(*) AS StreakLength
            FROM RankedGames
            GROUP BY UniqueId, StreakGroup
        )
        SELECT 
            MAX(StreakLength) AS MaxWinStreak
        FROM StreakCounts
        WHERE UniqueId = ?
        GROUP BY UniqueId;
    """, (unique_id,))

    data = cursor.fetchone()
    conn.close()

    return data[0] if data else 0  # Return 0 if no streak found

# 10. Get the win rate
def get_win_rate(conn, unique_id):
    """Get the user's win rate.
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("""
        WITH Wins AS (
            SELECT 
                UniqueId,
                GameId,
                MIN(Distance) AS ClosestDistance,
                MIN(DATE(DateTimeGuessed)) AS DayPlayed
            FROM GameDetail
            GROUP BY UniqueId, GameId
            HAVING MIN(Distance) = 0
        ),
        Losses AS (
            SELECT 
                UniqueId,
                GameId,
                MIN(Distance) AS ClosestDistance,
                MIN(DATE(DateTimeGuessed)) AS DayPlayed
            FROM GameDetail
            GROUP BY UniqueId, GameId
            HAVING MIN(Distance) <> 0
        )
        SELECT
            COUNT(wins.GameId) / COUNT(wins.GameId) + COUNT(losses.GameId) AS WinRate
        FROM Wins
        LEFT JOIN Losses ON losses.UniqueId = wins.UniqueId
        WHERE wins.UniqueId = ? OR losses.UniqueId
        GROUP BY wins.UniqueId;
    """, (unique_id,))

    data = cursor.fetchone()
    conn.close()

    return data[0] if data else 0  # Return 0 if no streak found

# 11. Get the total number of games played
def get_total_played(conn, unique_id):
    """Get the total numbers of games played
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(DISTINCT GameId)
        FROM GameDetail
        WHERE UniqueId = ?;
    """, (unique_id,))

    data = cursor.fetchone()
    conn.close()

    return data[0] if data else 0  # Return 0 if no streak found

# 12. Get values for the one screen stats chart
def get_chart_labels_values(win_stats):
    labels = [1, 2, 3, 4, 5, 6]
    if win_stats == None:
        values = [0, 0, 0, 0, 0, 0]
    else:
        stats_dict = {win_stats[0][1]:win_stats[0][2] for win_stats[0] in win_stats}
        values = [stats_dict.get(x, 0) for x in labels]

    return labels, values

# 13. Get all of a users stats
def get_all_stats(database, unique_id):
    conn = connect_to_database(database)
    win_stats = get_player_guess_stats(conn, unique_id)
    conn = connect_to_database(database)
    average_win_time = get_player_average_win_time(conn, unique_id)
    conn = connect_to_database(database)
    current_streak = get_current_streak(conn, unique_id)
    conn = connect_to_database(database)
    average_win_guesses = get_player_average_guess_stats(conn, unique_id)
    conn = connect_to_database(database)
    average_win_guesses = get_player_average_guess_stats(conn, unique_id)
    conn = connect_to_database(database)
    max_streak = get_max_streak(conn, unique_id)
    conn = connect_to_database(database)
    win_rate = get_win_rate(conn, unique_id)
    conn = connect_to_database(database)
    total_played = get_total_played(conn, unique_id)
    return win_stats, average_win_time, current_streak, average_win_guesses, max_streak, win_rate, total_played

# 14. Cookies functions
def accept_cookies():
    """Function to accept cookies."""
    consent_given = True
    session['cookie-consents'] = True
    return consent_given

def reject_cookies():
    """Function to reject cookies."""
    consent_given = False
    session['cookie-consents'] = False
    return consent_given

def check_consent():
    """Function to check the current consent status."""
    consent = session.get('cookie-consents')
    return consent

# 15. Date Checks

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

# 16. Database functions

# Create database connection
def connect_to_database(database_file):
    """Connect to a sqlite database

    Key arguments
    database_file -- location of sqlite database file
    """
    conn = sqlite3.connect(database_file, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

# Execute SQL
def execute_sql(conn, sql):
    """Execute SQL to a sqlite database

    Key arguments
    conn -- sqlite connection
    sql -- string of sqlite code
    """
    c = conn.cursor()
    c.execute(sql)

# Execute SQL and fetch one result
def execute_sql_fetch_one(conn, sql):
    """Execute SQL to a sqlite database

    and fetch answer (one answer only)
    Key arguments
    conn -- sqlite connection
    sql -- select string of sqlite code
    """
    c = conn.cursor()
    c.execute(sql)
    result = c.fetchone()
    return result

# Execute SQL and fetch all results
def execute_sql_fetch_all(conn, sql):
    """Execute SQL to a sqlite database

    and fetch all answers (multiple answers only)
    Key arguments
    conn -- sqlite connection
    sql -- select string of sqlite code
    """
    c = conn.cursor()
    c.execute(sql)
    result = c.fetchall()
    return result

# 17. Country Compare
# Function for cross references colours for two cleaned flags
def match_colours(image1, image2):
    """Compare two flags and show the difference between them

    Key arguments
    image1 -- first image that uses cv2.imread on an image file
    image2 -- comparison image that uses cv2.imread on an image file
    """
    # Check if images are the same initially
    if image1.shape != image2.shape:
        match = True
    else:
        match = False

    # Compare images pixel by pixel and calculate the absolute difference between each pixel
    difference = np.subtract(image1, image2)
    abs_difference = np.abs(difference)
    abs_difference_sum = np.sum(abs_difference, axis=2)

    # Set a threshold of zero and create a mask for above and below the threshold
    threshold = 0
    mask_match = abs_difference_sum <= threshold
    mask_no_match = abs_difference_sum > threshold
    green = [0, 255, 0]
    black = [0, 0, 0]

    # Set matches to green and no matches to black
    difference[mask_no_match] = black
    difference[mask_match] = green
        
    # Calculate the percentage difference between the flags
    calc_match = np.sum(mask_match) / (np.sum(mask_match) + np.sum(mask_no_match)) * 100
    perc_match = "{:.2f}%".format(calc_match)

    # Return result
    return match, difference, perc_match
    
def check_distance(coord1, coord2):
    """Compare two sets of lat-long coordinates and return the distance and direction between them

    Key arguments
    coord1 -- first set of coordinates eg. 42.546245,1.601554
    coord2 -- second set of coordinates to compare to, eg. 42.546245,1.601554
    """

    # Use geo to get the distance and bearing based on the latitude and longitude coordinates
    compare = geo.WGS84.Inverse(coord1[0], coord1[1], coord2[0], coord2[1])
    distance = compare['s12']
    bearing = compare['azi1']

    # Create list of cardinals
    cardinals = ["north", "north east", "east", "south east", "south", "south west", "west", "north west"]
    # Adjust bearing 
    bearing += 22.5
    bearing = bearing % 360

    # Convert bearing to index of the list
    bearing = int(bearing / 45) # values 0 to 7
    direction = cardinals [bearing]

    return distance, compare['azi1'], bearing, direction

def process_flags(imagepath):
    """Change flag to specific colour palette

    Key arguments
    imagepath -- path for image to change
    """
    # reference: https://sethsara.medium.com/change-pixel-colors-of-an-image-to-nearest-solid-color-with-python-and-opencv-33f7d6e6e20d
    colours = [(0, 0, 0) # black 
              ,(255, 255, 255) # white
              ,(206, 36, 36) # dark red
              ,(208, 16, 58) # red pink
              ,(0, 121, 52) # green
              ,(146, 22, 160) # purple
              ,(15, 65, 163) # blue
              ,(0, 175, 202) # bright blue
              ,(140, 185, 218) # light blue
              ,(222, 205, 182) # cream
              ,(250, 243, 65) # yellow
              ,(234, 203, 63) # gold
              ,(255, 128, 0) # orange
              ,(97, 54, 46) # brown
              ,(160, 160, 160) # grey
              ,(244, 142, 147) # pink
              ] 
        
    image = cv2.imread(imagepath)
    # convert BGR to RGB image
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    h,w,bpp = np.shape(image)

    # Change colors of each pixel
    # reference :https://stackoverflow.com/a/48884514/9799700
    for py in range(0,h):
        for px in range(0,w):
          
          #Used this part to find nearest color 
          #reference : https://stackoverflow.com/a/22478139/9799700
          input_color = (image[py][px][0],image[py][px][1],image[py][px][2])
          tree = sp.KDTree(colours) 
          ditsance, result = tree.query(input_color) 
          nearest_color = colours[result]

          image[py][px][0]=nearest_color[0]
          image[py][px][1]=nearest_color[1]
          image[py][px][2]=nearest_color[2]
    
    image = Image.fromarray(image)
    image = image.resize((800,530))
    image.save(imagepath.replace("flags","cleaned_flags"))


# 14. Main
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
    flaggle = os.path.join(THIS_FOLDER, "databases", "flaggle.db")

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
    #conn = connect_to_database(flaggle)
    #if conn is not None:
    #    # Execute required sql
    #    execute_sql(conn, drop_table_answer)
    #    execute_sql(conn, create_table_answer)
    #    execute_sql(conn, drop_table_games_detail)
    #    execute_sql(conn, create_table_games_detail)
    #    
    #    print("Database initialised.")
    #    
    #else:
    #    print("Error, no connection.")

    
    # Get details about the locations
    path = os.path.join(THIS_FOLDER, "static", "country latitude and longitude.csv")
    locations = pd.read_csv(path)
    # Generate list of country indexes
    countries = list(range(0, len(locations))) # List out index to select "random" country
    r.shuffle(countries)
    countries_sorted = sorted(locations['name'])

    # Start shuffle from today upon initialisation
    lastshuffled = date.today()
    country_index = 0

main()
#--------------------------------------------------

##### A P P L I C A T I O N #####------------------
# 1. Home page for website
# 2. Guess the country
# 3. Accept Cookies
# 4. Reject Cookies

# 1. Home page for website
@app.route("/")
def home():
    global flaggle
    ### Set up the game and fetch any required user information
    global locations
    global lastshuffled
    global country_index
    today = date.today()
    # When page is loaded, checks if we need to reshuffle the list
    check_shuffle = checkShuffle(lastshuffled, locations)
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
    todayscountryurl = os.path.join("images", "cleaned_flags", str(todayscountryid).lower() + ".png")
    # Get any existing id for user
    user_id, response = get_unique_id()

    # Get any current win stats
    win_stats, average_win_time, current_streak, average_win_guesses, max_streak, win_rate, total_played = get_all_stats(flaggle, user_id)
    
    labels, values = get_chart_labels_values(win_stats)
    
    ### Display any guessed countries for the user
    # Fetch todays game data
    conn = connect_to_database(flaggle)
    user_today_data = get_user_game_data_today(conn, user_id)
    conn.close()
    # Fetch id for last game played
    conn = connect_to_database(flaggle)
    game_id = get_user_last_game_id(conn, user_id)
    conn.close()
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
    guessed_image_path = [os.path.join("images", "cleaned_flags", str(x).lower() + ".png") for x in guessed_country_id]
    guessed_image_path = [{{ url_for('static', filename=x) }} for x in guessed_image_path]
    guessed_distances = [f"{int(round(x,0)/1000):,} km" if x != 0 else 0 for x in guessed_distances]
    guessed_directions_image_path = [os.path.join("images", "directions", str(x).lower() + ".png") for x in direction]
    guessed_directions_image_path = [{{ url_for('static', filename=x) }} for x in guessed_directions_image_path]
    # Convert country IDs into Country Names
    country_name_dict = dict(zip(locations['country'], locations['name']))
    guesses_country_name = [country_name_dict.get(code, code) for code in guessed_country_id]

    # Check player game conditions
    if any(x == 0 for x in guessed_distances) == True:
        # If the distance between countries is 0, they've got the right country and have won
        has_player_won = 1
        win_stats, average_win_time, current_streak, average_win_guesses, max_streak, win_rate, total_played = get_all_stats(flaggle, user_id)
        labels, values = get_chart_labels_values(win_stats)
    else:
        has_player_won = 0

    if len(guessed_country_id) == 6 and any(x == 0 for x in guessed_distances) != True:
        # If player has guessed six ttimes and none are a distance of 0, they have lost
        has_player_lost = 1
        win_stats, average_win_time, current_streak, average_win_guesses, max_streak, win_rate, total_played = get_all_stats(flaggle, user_id)
        labels, values = get_chart_labels_values(win_stats)
    else:
        has_player_lost = 0

    # Zip the lists together before passing to the template
    guesses = zip(guessed_image_path, guesses_country_name, guessed_distances, guessed_directions_image_path, image_url)
    
    # Set session ids
    session["user_id"] = user_id
    session["game_id"] = game_id   

    # Final Formatting
    win_rate = f"{win_rate:.0%}" # Win rate as a percentage
    total_guesses = 6 - len(guessed_country_id) # Total guesses remaining

    print(todayscountry)

    # Render the template normally
    rendered_template = render_template("index.html"
                           , country = todayscountry
                           , countryurl = {{ url_for('static', filename=todayscountryurl) }}
                           , countries = countries_sorted
                           , guesses = guesses
                           , won = has_player_won
                           , lost = has_player_lost
                           , win_stats = win_stats
                           , average_win_time = average_win_time
                           , current_streak = current_streak
                           , average_win_guesses = average_win_guesses
                           , max_streak = max_streak
                           , win_rate = win_rate
                           , total_played = total_played
                           , labels = labels
                           , values = values
                           , total_guesses = total_guesses)

    if response:  
        # Set the response body to the rendered template
        response.set_data(rendered_template)
        return response  # Return response with cookie set

    return rendered_template  # If no new cookie, return the page normally

# 2. Guess the country
@app.route("/guesscountry", methods=['GET', 'POST'])
def guesscountry():
    global conn
    global country_index

    # Get user id and game id
    user_id = session.get("user_id")  # Retrieve the ID from query parameters
    game_id = session.get("game_id")  # Retrieve the ID from query parameters

    # Get the country they have gussed
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

    distance_compare_result = check_distance(coord1, coord2)

    distance = distance_compare_result[0]
    direction = distance_compare_result[3]

    # Retreive the urls for the cleaned flag images for both guesses and todays country
    
    guessed_path = os.path.join("images", "cleaned_flags", str(guessedcountryid).lower() + '.png')
    answer_path = os.path.join("images", "cleaned_flags", str(todayscountryid).lower() + '.png')
    image1 = cv2.imread(guessed_path)
    image2 = cv2.imread(answer_path)

    # Match colours and save resulting image
    image_result = match_colours(image1, image2)
    cv2.imwrite(os.path.join("guesses", "output_" + str(todayscountryid).lower() + "_" + str(guessedcountryid).lower() + ".png"), image_result[1])
    guessed_image_result_path = os.path.join("guesses", "output_" + str(todayscountryid).lower() + "_" + str(guessedcountryid).lower() + ".png")

    # Store Results in Database
    try:
        conn = connect_to_database(flaggle)
        insert_game_guess(conn, user_id, game_id, guessedcountryid, distance, direction, guessed_image_result_path)
        conn.close()
    except:
        return redirect("error.html")
    
    return redirect("/")

# 3. Accept Cookies
@app.route("/accept", methods=["GET"])
def accept():
    # Run accept cookies function
    accept_cookies()
    return redirect("/")

# 4. Reject Cookies
@app.route("/reject", methods=["GET"])
def reject():
    # Run reject cookies function
    reject_cookies()
    return redirect("/")

#--------------------------------------------------

##### I N I T I A L I S A T I O N #####
if __name__ == '__main__':
    main()
    # If statement to prevent run when hosting in PythonAnywhere
    if 'liveconsole' not in gethostname():
        app.run() # app.run(debug=True, port = 8000) to set different port

#--------------------------------------------------