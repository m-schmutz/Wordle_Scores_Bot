#!/bin/python3
import sqlite3 as sql
from datetime import datetime
from os import path, remove
import time

DB_PATH = './bot_database/test.db'

def date_to_int():
    return int(datetime.now().date().isoformat().replace('-', ''))

class DoubleSubmit(Exception):
    '''Exception raised if user attempts to submit twice on the same day'''

class BotDatabase:
    '''
    Database class. Contains two member variables _database and _users. 
    _database is a sqlite3 database connection where data is stored.
    _users is a python dictionary containing the usernames of users that are in the database,
    each user maps to the date of their last submission 
    '''
    def __init__(self, db_path:str):
        '''
        BotDatabase(path:str) -> BotDatabase object with sqlite3 database stored at specified path
        For example: BotDatabase('/path/to/database')
        '''
        
        # initialize sqlite database at specified path
        self._database = sql.connect(db_path)

        # initialize dictionary to contain users and their last submission date
        self._users = dict()

        # initialize cursor
        __cur = self._database.cursor()

        # execute sql script to initialize the sqlite database
        __cur.executescript('''

        CREATE TABLE User_Data (
            username varchar(32), 
            attempts int, 
            solves int, 
            guesses int, 
            greens int, 
            yellows int, 
            curr_streak int, 
            max_streak int, 
            last_solve int, 
            PRIMARY KEY (username)
            ); 

        CREATE TABLE Group_Data (
            attempts int, 
            solves int, 
            guesses int,
            greens int, 
            yellows int 
            ); 

        CREATE TRIGGER Update_Max AFTER UPDATE ON User_Data
            BEGIN
            UPDATE User_Data SET max_streak = curr_streak 
            WHERE username = NEW.username AND curr_streak > max_streak;
            END;
            
        INSERT INTO Group_Data (
            attempts, 
            solves, 
            guesses, 
            greens, 
            yellows
            )
            VALUES (
                0, 
                0, 
                0, 
                0, 
                0 
            );''')
        
        # close the cursor
        __cur.close()

        # commit the changes to the database
        self._database.commit()

    def get_stats(self, username:str):
        '''
        Method returns the stats on the specified user
        Stats returned: 
        '''
        __cur = self._database.cursor()
        __raw = __cur.execute(f'''SELECT * FROM User_Data WHERE username = '{username}';''').fetchall()
        print(__raw)
        __cur.close()

    def _get_update_values(self, solved:int, __last_solve:int, date:int):
        # increase solves if user solved the wordle; otherwise solves stays the same
        __solves_update = 'solves + 1' if solved else 'solves'

        # increment streak if user has solved consecutively; otherwise streak will not be incremented
        __continue_streak = True if (date - __last_solve) == 1 else False

        # last solve is set to current date if wordle solved; otherwise last solve stays the same
        __last_solve_update = date if solved else __last_solve

        # increment streak 
        if solved and __continue_streak:
            __streak_update = 'curr_streak + 1'
        
        # set streak to 1 if this is the start of a new streak
        elif solved:
            __streak_update = '1'

        # set streka to 0 if user did not solve wordle today
        else:
            __streak_update = '0'

        # return computed values
        return __solves_update, __streak_update, __last_solve_update

    def _update_user(self, username:str, solved:bool, guesses:int, greens:int, yellows:int, date:int):

        # initialize cursor
        __cur = self._database.cursor()

        # get the last solve date for this user
        __last_solve = __cur.execute(f'''SELECT last_solve FROM User_Data WHERE username = '{username}';''').fetchone()[0]

        # get the update values for the database
        __solves_update, __streak_update, __last_solve_update = self._get_update_values(solved, __last_solve, date)

        # execute sql script to update data in database for this user
        __cur.executescript(f'''
            UPDATE User_Data SET attempts = attempts + 1 WHERE username = '{username}';
            UPDATE User_Data SET solves = {__solves_update} WHERE username = '{username}';
            UPDATE User_Data SET guesses = guesses + {guesses} WHERE username = '{username}';
            UPDATE User_Data SET greens = greens = greens + {greens} WHERE username = '{username}';
            UPDATE User_Data SET yellows = yellows + {yellows} WHERE username = '{username}';
            UPDATE User_Data SET curr_streak = {__streak_update} WHERE username = '{username}';
            UPDATE User_Data SET last_solve = {__last_solve_update} WHERE username = '{username}'; 

            UPDATE Group_Data SET attempts = attempts + 1;
            UPDATE Group_Data SET solves = {__solves_update};
            UPDATE Group_Data SET guesses = guesses + {guesses};
            UPDATE Group_Data SET greens = greens + {greens};
            UPDATE Group_Data SET yellows = yellows + {yellows};
        ''')

        # close cursor
        __cur.close()

        # commit changes to the database
        self._database.commit()

    def _add_user(self, username:str, solved:bool, guesses:int, greens:int, yellows:int, date:int):
        
        __cur = self._database.cursor()

        # add user to the _users dictionary
        self._users[username] = date

        # attempts set to 1
        __attempts_insert = 1
        
        # solves and streak set to 1 if solved; otherwise 0
        __solves_insert = __streak_insert = 1 if solved else 0

        # last_solve will set to todays date if solved; otherwise set to 0
        __date_insert = date if solved else 0

        # execute sql script to add new user to the database
        __cur.executescript(f'''
            INSERT INTO User_Data (
                username, 
                attempts, 
                solves, 
                guesses, 
                greens, 
                yellows, 
                curr_streak, 
                max_streak, 
                last_solve)
                Values (
                    '{username}', 
                    {__attempts_insert}, 
                    {__solves_insert}, 
                    {guesses}, 
                    {greens}, 
                    {yellows}, 
                    {__streak_insert}, 
                    {__streak_insert}, 
                    {__date_insert});
        ''')

        # close the cursor
        __cur.close()

        # commit the changes to the database
        self._database.commit()

    def submit_data(self, username:str, solved:bool, guesses:int, greens:int, yellows:int):
        '''Given the username and info on attempt, user stats are updated in the database. A user is added to the database if
        they are a new user. Method will raise DoubleSubmit exception if method is called on the same user twice or more on one day'''

        # grab todays date in integer form (YYYYMMDD)
        date = date_to_int()

        # check if the user is in the database
        if username in self._users:

            # get the date of their last submission 
            __last_submit = self._users[username]

            # check if this user has already submitted this day
            if __last_submit == date:
                
                # raise DoubleSubmit exception
                raise DoubleSubmit('already submitted today')

            # if we get here, this is a new submission for today. Update database
            self._update_user(username, solved, guesses, greens, yellows, date)

            # update the last submission date
            self._users[username] = date

        # if user is not in _users, add new user and update database
        else:
            # add user to the _users registry
            self._users[username] = date
            
            # add user to the database
            self._add_user(username, solved, guesses, greens, yellows, date)

            
if __name__ == '__main__':
    remove(DB_PATH)
    db = BotDatabase(DB_PATH)

    db.submit_data('mario', True, 1, 1, 1)

    db.get_stats('mario')
