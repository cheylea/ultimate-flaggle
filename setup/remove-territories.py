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
countries = df['CountryId'].values.tolist() # List out index to select "random" country
print(countries)
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
total_days = [date.today() + timedelta(days=x) for x in total_days]

# Insert data
conn = db.connect_to_database(flaggle)

# Remove going forward countries
today = date.today()
sql = f"DELETE FROM Answer WHERE Date >= '{today}'"

db.execute_sql(conn, sql)

for answer, day in zip(answers, total_days):
    sql = "INSERT INTO Answer (CountryId, Date) VALUES (" + str(answer) + ", '" + str(day) + "')"
    db.execute_sql(conn, sql)
print("Finished adding answers")


# Countries
drop_table_country = """DROP TABLE IF EXISTS Country; """
create_table_country = """ CREATE TABLE IF NOT EXISTS Answer (
                            CountryId int PRIMARY KEY AUTOINCREMENT,
                            Country text,
                            Latitude,
                            Longitude,
                            Name
                        ); """

# Make connection to flaggle database file
conn = db.connect_to_database(flaggle)

if conn is not None:
    # Execute required sql
    db.execute_sql(conn, drop_table_country)
    db.execute_sql(conn, create_table_country)
    df.to_sql("Country", conn, if_exists='replace', index=False)
    print("Database initialised.")
    
else:
    print("Error!")