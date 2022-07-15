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
    Database class. Contains two member variables database and users. 
    database is a sqlite3 database connection where data is stored
    users is a python set containing the usernames of users that are in the database 
    '''
    def __init__(self, db_path:str):
        '''
        BotDatabase(path:str) -> BotDatabase object with sqlite3 database stored at specified path
        For example: BotDatabase('/path/to/database')
        '''
        self._database = sql.connect(db_path)
        self._users = dict()
        __cur = self._database.cursor()
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
        
        __cur.close()
        self._database.commit()

    def get_stats(self, username:str):
        __cur = self._database.cursor()
        __raw = __cur.execute(f'''SELECT * FROM User_Data WHERE username = '{username}';''').fetchall()
        print(__raw)

    def _get_update_values(self, solved:int, last_solve:int, date:int):
        # determine whether solves will be incremented
        __solves_update = 'solves + 1' if solved else 'solves'

        # determine if user solved the wordle the previous day
        __prev_solve = True if (date - __last_solve) == 1 else False

        # increase streak if user solved today and day before
        if solved and __prev_solve:
            __streak_update = 'curr_streak + 1'
        
        # set streak to 1 if this is the start of a new streak
        elif solved:
            __streak_update = '1'

        # set streka to 0 if user did not solve wordle today
        else:
            __streak_update = '0'

    def _update_user(self, username:str, solved:int, guesses:int, greens:int, yellows:int, date:int):

        # initialize cursor
        __cur = self._database.cursor()

        # get last solve date
        __last_solve = __cur.execute(f'''SELECT last_solve FROM User_Data WHERE username = '{username}';''').fetchone()[0]

    def _add_user(self, username:str, solved:int, guesses:int, greens:int, yellows:int, date:int):
        pass

    def submit_data(self, username:str, solved:bool, guesses:int, greens:int, yellows:int):
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
    # remove(DB_PATH)
    # db = BotDatabase(DB_PATH)

    # db.submit_data('mario', 1, 1, 1, 1, 1)

    date = date_to_int()

    __last_solve = 20220713

    r = True if (date - __last_solve) == 1 else False


    print(r)









# # create cursor
#         __cur = self._database.cursor()
#         # __date = int(datetime.now().date().isoformat().replace('-', ''))
#         __date = date

#         # if user is in the database
#         if username in self._users:

#             # determine whether the solve stat will be incremented or not
#             __solve_update = 'solves + 1' if solved else 'solves'

#             # get value of the last solve date
#             __last_solve = __cur.execute(f'''SELECT last_solve FROM User_Data WHERE username = '{username}';''').fetchone()[0]

#             # determine if user solved the wordle the day before
#             __prev_solved = True if (__date - __last_solve) == 1 else False

#             # determine if user's current streak will be incremented or set to 0
#             __curr_streak = 'curr_streak + 1' if solved and __prev_solved else '0'

#             # determine if the last solve date will be updated or stay the same
#             __date_update = str(__date) if solved else 'last_solve'

#             # execute sql script to update the database
#             __cur.executescript(f'''
#                 UPDATE User_Data SET attempts = attempts + 1 WHERE username = '{username}';
#                 UPDATE User_Data SET solves = {__solve_update} WHERE username = '{username}';
#                 UPDATE User_Data SET guesses = guesses + {guesses} WHERE username = '{username}';
#                 UPDATE User_Data SET greens = greens + {greens} WHERE username = '{username}';
#                 UPDATE User_Data SET yellows = yellows + {yellows} WHERE username = '{username}';
#                 UPDATE User_Data SET last_solve = {__date_update} WHERE username = '{username}';
#                 UPDATE User_Data SET curr_streak = {__curr_streak} WHERE username = '{username}';

#                 UPDATE Group_Data SET attempts = attempts + 1;
#                 UPDATE Group_Data SET solves = {__solve_update};
#                 UPDATE Group_Data SET guesses = guesses + {guesses};
#                 UPDATE Group_Data SET greens = greens + {greens};
#                 UPDATE Group_Data SET yellows = yellows + {yellows};
#             ''')

#             # close cursor to conserve memory
#             __cur.close()

#             # commit changes to the database
#             self._database.commit()

#         else:
#             self._users.add(username)

#             __solves_insert = '1' if solved else '0'
#             __date_insert = str(__date) if solved else '0' 

#             __cur.executescript(f'''
#                 INSERT INTO User_Data (
#                     username, 
#                     attempts, 
#                     solves, 
#                     guesses, 
#                     greens, 
#                     yellows, 
#                     curr_streak, 
#                     max_streak, 
#                     last_solve)
#                     Values (
#                         '{username}', 
#                         1, 
#                         {__solves_insert}, 
#                         {guesses}, 
#                         {greens}, 
#                         {yellows}, 
#                         {__solves_insert}, 
#                         {__solves_insert}, 
#                         {__date_insert});

#                 UPDATE Group_Data SET attempts = attempts + 1;
#                 UPDATE Group_Data SET solves = {__solves_insert};
#                 UPDATE Group_Data SET guesses = guesses + {guesses};
#                 UPDATE Group_Data SET greens = greens + {greens};
#                 UPDATE Group_Data SET yellows = yellows + {yellows};
            
#             ''')
            
#             __cur.close()
#             self._database.commit()