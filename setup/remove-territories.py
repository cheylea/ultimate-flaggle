import os
from pathlib import Path
from DatabaseFunctions import DatabaseFunctions as db
import pandas as pd # for handling dataframes
import random as r
from collections import Counter
from datetime import date, timedelta

THIS_FOLDER = Path(__file__).parent.resolve()

## Create table for the flaggle game details database
absolute_path = os.path.dirname(__file__)
directory_path = absolute_path.replace("\setup","")
flaggle = os.path.join(directory_path, "src", "databases", "flaggle.db")
print(flaggle)

# Get the countries dataframe
path = os.path.join(THIS_FOLDER, "CountryCoordinates.csv")
locations = pd.read_csv(path)
df = pd.DataFrame(locations)

# Generate Answers
r.seed(10)
# Get details about the locations
# Generate list of country index for next 10
countries = list(range(0, len(df))) # List out index to select "random" country
countries = countries * 100

def restricted_shuffle(countries):
    count = Counter(countries)  # Count occurrences of each item
    unique_items = list(count.keys())
    stretch_size = len(unique_items)  # The max stretch size before a repeat
    
    # Create a pool of all elements
    shuffled = []
    
    # Source: Chat GPT
    while sum(count.values()) > 0:
        batch = []
        available = [item for item in unique_items if count[item] > 0]
        r.shuffle(available)  # Randomize the available items
        
        for item in available[:stretch_size]:  # Pick up to stretch_size unique elements
            batch.append(item)
            count[item] -= 1
        
        shuffled.extend(batch)  # Append batch to the final shuffled list

    return shuffled

answers = restricted_shuffle(countries)
total_days = list(range(0, len(answers)))
total_days = [date.today() + timedelta(days=1) + timedelta(days=x) for x in total_days]

# Insert data
conn = db.connect_to_database(flaggle)

# Remove going forward countries
sql = 'DELETE FROM Answer WHERE Date > ''2025-04-01;'''
db.execute_sql(conn, sql)

for answer, day in zip(answers, total_days):
    sql = "INSERT INTO Answer (CountryId, Date) VALUES (" + str(answer) + ", '" + str(day) + "')"
    db.execute_sql(conn, sql)
print("Finished adding answers")