#!/usr/bin/python3
# Set of Python functions for comparing two flags

### Imports
import sqlite3

### Database Functions

class DatabaseFunctions:
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