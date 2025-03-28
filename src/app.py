#!/usr/bin/python3
# Ultimate Flaggle

###### I M P O R T S #####------------------------
import os
import datetime as dt
from datetime import date
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
# 12. Get values for the on screen stats chart
# 13. Get todays country
# 14. Lookup a countries details by index
# 15. Get all of a users stats
# 16. Cookies functions
# 17. Country Compare

# 1. User UniqueId generation 
def get_unique_id():
    """Get or create a unique ID for tracking depending on cookie consent."""
    consent_status = session.get("consent_status")
    unique_id = request.cookies.get("unique_id")  # Check if cookie exists

    # If unique_id exists, reset its expiry and return it
    if unique_id:  
        response = make_response(unique_id)
        response.set_cookie("unique_id", unique_id, max_age=60*60*24*365*10)
        session["user_id"] = unique_id
        return unique_id, consent_status, response

    # If consent has been given, store the cookie
    if consent_status == "accepted":
        if unique_id == None:
            unique_id = str(uuid.uuid4())
        response = make_response(unique_id)
        response.set_cookie("unique_id", unique_id, max_age=60*60*24*365*10)
        session["user_id"] = unique_id
        return unique_id, consent_status, response
    
    # If consent has not been given, do not store as cookie but use a session cookie
    if consent_status == "rejected":  
        unique_id = session.get("user_id")
        if unique_id == None:
            unique_id = str(uuid.uuid4())
        session["user_id"] = unique_id
        response = make_response(unique_id)
        return unique_id, consent_status, response

    # If no cookie exists and no consent, return nothing
    return unique_id, consent_status, None

# 2. Get the users game data from today
def get_user_game_data_today(conn, unique_id):
    """Fetch user game data from the database for today.
    
    Key arguments
    conn -- connection to the sqlite database
    uniqueid -- unique id for a given user
    """
    cursor = conn.cursor()

    cursor.execute("""SELECT gd.Country, Distance, Direction, ComparedImageUrl, Name FROM GameDetail gd
                      JOIN Country c ON c.Country = gd.Country
                      WHERE UniqueId = ? AND date(DateTimeGuessed) = ? ORDER BY DateTimeGuessed DESC""", (unique_id, date.today()))
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
    INSERT INTO GameDetail (UniqueId, GameId, DateTimeGuessed, Country, Distance, Direction, ComparedImageUrl)
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
                    WHERE UniqueId = ?
                    GROUP BY TotalGuesses""", (unique_id,))
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
    return round(float(data[0]),2) if data else 0

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
    return round(float(data[0]),2) if data else 0

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
            CAST(COUNT(DISTINCT wins.GameId) as float) / (COUNT(DISTINCT wins.GameId) + COUNT(DISTINCT losses.GameId)) AS WinRate
        FROM Wins
        LEFT JOIN Losses ON losses.UniqueId = wins.UniqueId
        WHERE wins.UniqueId = ? OR losses.UniqueId = ?
        GROUP BY wins.UniqueId;
    """, (unique_id, unique_id,))

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

# 12. Get values for the on screen stats chart
def get_chart_labels_values(win_stats):
    """Get the labels and values from a dataset returns from a sqlite database
    
    Key arguments
    winstats -- result from sqlite database with number of times a player guessed 1-6
    """
    labels = [1, 2, 3, 4, 5, 6]
    if win_stats == None:
        values = [0, 0, 0, 0, 0, 0]
    else:
        stats_dict = {win_stats[0][1]:win_stats[0][2] for win_stats[0] in win_stats}
        values = [stats_dict.get(x, 0) for x in labels]

    return labels, values

# 13. Get todays country
def get_todays_country(conn):
    """Execute SQL to get todays country

    Key arguments
    conn -- sqlite connection
    sql -- select string of sqlite code
    """
    sql = "SELECT CountryId FROM Answer WHERE Date = '" + str(date.today()) + "'"
    c = conn.cursor()
    c.execute(sql)
    result = c.fetchone()
    return result[0]

# 14. Lookup a countries details by index
def get_country_details(conn, countryindex):
    """Execute SQL to get a countries details

    Key arguments
    conn -- sqlite connection
    sql -- select string of sqlite code
    """
    sql = "SELECT Country, Latitude, Longitude, Name FROM Country WHERE CountryId = '" + str(countryindex) + "'"
    c = conn.cursor()
    c.execute(sql)
    result = c.fetchall()

    if result:
        code = result[0][0]
        latitude = result[0][1]
        longitude = result[0][2]
        name = result[0][3]
        url = url_for('static', filename="images/cleaned_flags/" + str(code).lower() + ".png")
    else:
        return None, None, None, None, None
    return code, latitude, longitude, name, url

# 15. Get all of a users stats
def get_all_stats(database, unique_id):
    """Execute every sql result required for game start up
    
    Key arguments
    database -- The database to connect to
    unique_id -- The unique id to filter on when running start up stats
    """
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

# 16. Cookies functions
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

# 17. Database functions

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

    lat_diff = coord2[0] - coord1[0]
    lon_diff = coord2[1] - coord1[1]

    if abs(lat_diff) > abs(lon_diff):  # More movement in latitude
        primary_direction = "north" if lat_diff > 0 else "south"
        secondary_direction = "east" if lon_diff > 0 else "west"
    else:  # More movement in longitude
        primary_direction = "north" if lat_diff > 0 else "south"
        secondary_direction = "east" if lon_diff > 0 else "west"

    # Handle cases where movement is mostly in one direction
    if abs(lat_diff) < 5:  # Almost purely east/west
        direction = primary_direction
    if abs(lon_diff) < 5:  # Almost purely north/south
        direction = primary_direction
    else:
        direction =  primary_direction + ' ' + secondary_direction
    
    return direction, distance

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



#--------------------------------------------------

##### A P P L I C A T I O N #####------------------
# 1. Home page for website
# 2. Guess the country
# 3. Accept Cookies
# 4. Reject Cookies
# 5. Store the cookie consent in Flask

# 1. Home page for website
@app.route("/")
def home():
    ### Set up the game and fetch any required user information
    #consent_status = request.json.get("cookie-consent") 

    flaggle = os.path.join(THIS_FOLDER, "databases", "flaggle.db") # Get the database path
    conn = connect_to_database(flaggle) # Connect to database
    todayscountryindex = get_todays_country(conn) # Get todays country index

    # Get todays country details
    todayscountryid, todayscountrylat, todayscountrylong, todayscountry, todayscountryurl = get_country_details(conn, todayscountryindex)
    countries = execute_sql_fetch_all(conn, "SELECT Name FROM Country ORDER BY Name;")
    countries = [x[0] for x in countries ]
    conn.close()
    # Get any existing id for users
    user_id, consent_status, response = get_unique_id()
    print(user_id)
    print(consent_status)

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
        guessed_country_id, guessed_distances, direction, image_url, name = zip(*user_today_data)
    else:
        guessed_country_id, guessed_distances, direction, image_url, name = [], [], [], [], []  # Empty lists if no data

    # Format the select results to display in the template
    guessed_country_id = list(guessed_country_id)
    guessed_image_path = [url_for('static', filename=f'images/cleaned_flags/{str(x).lower()}.png') for x in guessed_country_id]
    #guessed_distances = [f"{int(round(x,0)/1000):,} km" if x != 0 else 0 for x in guessed_distances]
    guessed_distances = [ # Put distances into buckets
    "Found!" if int(round(x, 0) / 1000) == 0 else
    "Scorching / Nearby" if int(round(x, 0) / 1000) < 500 else
    "Hot / Close" if int(round(x, 0) / 1000) < 1000 else
    "Warm / Same Viscinity" if int(round(x, 0) / 1000) < 2000 else
    "Chilly / Distant" if int(round(x, 0) / 1000) < 5000 else
    "Cold / Far" if int(round(x, 0) / 1000) < 10000 else
    "Freezing / Remote"
    for x in guessed_distances
    ]
    direction = list(direction)
    guessed_directions_image_path = [url_for('static', filename=f'images/directions/{str(x).lower()}.png') for x in direction]
    guesses_country_name = list(name)
    

    total_guesses = 6 - len(guessed_country_id) # Total guesses remaining

    # Check player game conditions
    if any(x == "Found!" for x in guessed_distances) == True:
        # If the distance between countries is 0, they've got the right country and have won
        has_player_won = 1
        win_stats, average_win_time, current_streak, average_win_guesses, max_streak, win_rate, total_played = get_all_stats(flaggle, user_id)
        labels, values = get_chart_labels_values(win_stats)
    else:
        has_player_won = 0

    if len(guessed_country_id) == 6 and any(x == "Found!" for x in guessed_distances) != True:
        # If player has guessed six times and none are a distance of 0, they have lost
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

    # Other Formatting
    win_rate = f"{win_rate:.0%}" # Win rate as a percentage
    
    print(todayscountry)

    # Render the template normally
    rendered_template = render_template("index.html"
                           , country = todayscountry
                           , countryurl = todayscountryurl
                           , countries = countries
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
    flaggle = os.path.join(THIS_FOLDER, "databases", "flaggle.db") # Get the database path
    conn = connect_to_database(flaggle) # Connect to database
    # Get user id and game id
    user_id = session.get("user_id")  # Retrieve the ID from query parameters
    game_id = session.get("game_id")  # Retrieve the ID from query parameters
    print(user_id)
    print(game_id)

    # Get the country they have gussed
    guessedcountry = request.form['guessedcountry']
    guessedcountry = guessedcountry.replace("'", "''")  # Double the single quotes
    guessedcountryindex = execute_sql_fetch_one(conn, "SELECT CountryId FROM Country WHERE Name = '" + guessedcountry + "'")
    guessedcountryindex = guessedcountryindex[0]
    # Get todays country
    todayscountryindex = get_todays_country(conn)
    
    # Perform Country Compare Functions
    # Get values for the guessed country
    guessedcountryid, guessedcountrylat, guessedcountrylong, guessedcountry, guessedcountryurl = get_country_details(conn, guessedcountryindex)

    # Get values for todays country
    todayscountryid, todayscountrylat, todayscountrylong, todayscountry, todayscountryurl = get_country_details(conn, todayscountryindex)

    # Calculate the distance and direction between the two countries
    coord1 = [guessedcountrylat, guessedcountrylong]
    coord2 = [todayscountrylat, todayscountrylong]

    distance_compare_result = check_distance(coord1, coord2)

    distance = distance_compare_result[1]
    direction = distance_compare_result[0]

    # Retreive the urls for the cleaned flag images for both guesses and todays country
    # Get the absolute path of the static folder
    static_folder = app.static_folder  

    # Build the correct path
    guessed_path = os.path.join(static_folder, "images", "cleaned_flags", f"{str(guessedcountryid).lower()}.png")
    answer_path = os.path.join(static_folder, "images", "cleaned_flags", f"{str(todayscountryid).lower()}.png")
    image1 = cv2.imread(guessed_path)
    image2 = cv2.imread(answer_path)

    # Match colours and save resulting image
    image_result = match_colours(image1, image2)
    cv2.imwrite(os.path.join(static_folder, "guesses", "output_" + str(int((int(todayscountryindex) / 14) * 126 + 6969 - 420)).lower() + "_" + str(guessedcountryid).lower() + ".png"), image_result[1])
    guessed_image_result_path = url_for('static', filename=f'guesses/output_{str(int((int(todayscountryindex) / 14) * 126 + 6969 - 420)).lower()}_{str(guessedcountryid).lower()}.png')

    conn.close()

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

# 5. Store the cookie consent in Flask
@app.route('/store_consent_status', methods=['POST'])
def store_consent_status():
    """Save the localStorage consent status into Flask session."""
    data = request.get_json()
    session["consent_status"] = data.get("cookie-consent")
    return jsonify({"message": "Consent status stored", "consent_status": session["consent_status"]})

#--------------------------------------------------

##### I N I T I A L I S A T I O N #####
if __name__ == '__main__':
    # If statement to prevent run when hosting in PythonAnywhere
    if 'liveconsole' not in gethostname():
        app.run() # app.run(debug=True, port = 8000) to set different port

#--------------------------------------------------
