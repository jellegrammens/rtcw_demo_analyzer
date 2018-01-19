# Generic class that can be used to connect to a MySQL database
 
import sqlite3
import logging
import datetime
import time
import pandas as pd
import re
 
class sqlite3_connector:
    def __init__(self, path_to_db):
        self.path_to_db = path_to_db
        self.connect_to_db()
 
    def connect_to_db(self):
        self.db = sqlite3.connect(self.path_to_db)
 
    def execute_query(self, query, attempt_count=0):
        cursor = self.db.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def get_table_names(self):
        """ Returns a list of all table names """
        out = self.execute_query('select name from sqlite_master where type = "table"')
        return pd.DataFrame(list(out))[0].values

    def get_columns_from_tables(self, table_name):
        sql = 'SELECT * FROM ' + table_name
        data = self.db.execute(sql)
        column_names = list(map(lambda x: x[0], data.description))
        return column_names

    def get_table_as_df(self, table_name):
        """Fetch a complete table from the database and format it as a pandas dataframe"""
        sql = 'SELECT * FROM ' + table_name
        start_time = time.time()
        data = self.execute_query(sql)
        column_names = self.get_columns_from_tables(table_name)
        duration_seconds = round(time.time() - start_time, 2)
        print (str(table_name) + " table fetched in " + str(duration_seconds) + " seconds")
        mydf = pd.DataFrame.from_records(list(data), columns=column_names)
        return mydf

