import sqlite3 as sql
from datetime import datetime
from os import path
from typing import Tuple

LTRS_IN_GUESS = 5

# set DEBUG to True if you want to ignore double submits
DEBUG = False

class UserStats:
    '''
    Object to contain user stats returned from the database

    ---
    #### Members
    - attempts 
    - solves
    - guesses
    - greens
    - yellows
    - curr_streak
    - max_streak
    - total_letters
    - avg_guesses
    - green_rate
    - yellow_rate

    '''
    def __init__(self, __raw:tuple):
        _, attempts, solves, guesses, greens, yellows, curr_streak, max_streak, last_solve = __raw

        self.attempts = attempts
        self.solves = solves
        self.guesses = guesses
        self.greens = greens
        self.yellows = yellows
        self.curr_streak = curr_streak
        self.max_streak = max_streak
        
        _total_letters = guesses * LTRS_IN_GUESS
        self.total_letters = _total_letters

        self.avg_guesses = guesses / attempts

        self.green_rate = (greens / _total_letters) * 100
        self.yellow_rate = (yellows / _total_letters) * 100

    def __str__(self) -> str:
        return f'''
        attempts = {self.attempts}
        solves = {self.solves}
        guesses = {self.guesses}
        average guesses = {self.avg_guesses}
        greens = {self.greens}
        yellows = {self.yellows}
        current streak = {self.curr_streak}
        max streak = {self.max_streak}
        total letters = {self.total_letters}
        green rate = {self.green_rate}
        yellow rate = {self.yellow_rate}
        '''
        

class DoubleSubmit(Exception):
    '''Exception raised if user attempts to submit twice on the same day'''
    
    # takes in username to print out whihc user is attempting to submit twice 
    def __init__(self, username) -> None:
        self.username = username    

    # set __module__ to exception module (nice print out message)
    ## this can be taken out later
    __module__ = Exception.__module__
    
    # print string including username of user that has attempted to submit twice
    def __str__(self):
        return f'{self.username} has already submitted today'

class BotDatabase:
    '''
    Database class. Contains one member _database. 
    _database is a sqlite3 database connection where data is stored.
    '''
    def __init__(self, db_path:str) -> None:
        '''
        BotDatabase(path:str) -> BotDatabase object with sqlite3 database stored at specified path
        For example: BotDatabase('/path/to/database')
        If database file already exists, it will be used as the database
        '''
        # determine if the file at db_path already exists
        exists = path.exists(db_path)

        # initialize sqlite database at specified path
        self._database = sql.connect(db_path)

        # if the database did not previously exist, initialize the new one
        if not exists:

            # initialize cursor
            _cur = self._database.cursor()

            # execute sql script to initialize the sqlite database
            _cur.executescript('''

            CREATE TABLE User_Data (
                username varchar, 
                games int, 
                wins int, 
                guesses int, 
                greens int, 
                yellows int, 
                uniques int, 
                guess_distro varchar, 
                last_solve int, 
                last_submit int, 
                curr_streak int, 
                max_streak int, 
                PRIMARY KEY (username)
                ); 

            CREATE TABLE User_Stats (
                username varchar,
                win_rate float,
                avg_guesses float,
                green_rate float,
                yellow_rate float,
                FOREIGN KEY (username) REFERENCES User_Data(username)
                );

            CREATE TRIGGER Update_Max AFTER UPDATE ON User_Data
                BEGIN
                UPDATE User_Data SET max_streak = curr_streak 
                WHERE username = NEW.username AND curr_streak > max_streak;
                END;''')
            
            # close the cursor
            _cur.close()

        # commit the changes to the database
        self._database.commit()

    def __del__(self) -> None:
        # close connection to database
        self._database.close()

    def get_user_stats(self, username:str) -> UserStats:
        '''
        Method returns the stats on the specified user
        Stats returned: 
        '''
        # initialize cursor
        _cur = self._database.cursor()

        # get user data from the database
        _raw = _cur.execute(f'''SELECT * FROM User_Data WHERE username = '{username}';''').fetchone()
        
        # close the cursor
        _cur.close()

        # initialize UserStats object with values from database
        user_stats = UserStats(_raw)

        # return UserStats object
        return user_stats

    def _get_update_values(self, raw:Tuple, win:bool, guesses:int, greens:int, yellows:int, uniques:int, date:int):
        
        # extract fields from tuple
        _games, _wins, _guesses, _greens, _yellows, _uniques, _distro_str, _last_solve, _curr_streak = raw



        # games update value
        _games_update = _games + 1

        # wins update value
        _wins_update = _wins + win

        # guesses update value
        _guesses_update = _guesses + guesses

        # greens update value
        _greens_update = _greens + greens

        # yellows update value
        _yellows_update = _yellows + yellows

        # uniques update value
        _uniques_update = _uniques + uniques

        # increment streak if user has solved consecutively; otherwise streak will not be incremented
        _continue_streak = (date - _last_solve) == 1 

        # last solve is set to current date if wordle solved; otherwise last solve stays the same
        _last_solve_update = date if win else _last_solve



        # increment streak 
        if win and _continue_streak:
            _streak_update = _curr_streak + 1
        
        # set streak to 1 if this is the start of a new streak
        elif win:
            _streak_update = 1

        # set streka to 0 if user did not solve wordle today
        else:
            _streak_update = 0



        # if they win, update the guess distribution
        if win:
            # convert string to dictionary
            temp_dict = dict( (k,v) for k,v in zip(range(1,7), map(int, _distro_str.split())))

            # update dictionary
            temp_dict[guesses] += 1

            # convert dictionary back to string
            _distro_str_update = ' '.join(map(str, temp_dict.values()))
            
        # otherwise it stays the same
        else:
            _distro_str_update = _distro_str



        # win rate update value
        _win_rate_update = _wins_update / _games_update

        # avg guesses update value
        _avg_guesses_update = _guesses_update / _games_update

        # green rate update value
        _green_rate_update = _greens_update / _uniques_update

        # yellow rate update value 
        _yellow_rate_update = _yellows_update / _uniques_update



        # return computed values
        return _games_update, \
        _wins_update, \
        _guesses_update, \
        _greens_update, \
        _yellows_update, \
        _uniques_update, \
        _last_solve_update, \
        _streak_update, \
        _distro_str_update, \
        _win_rate_update, \
        _avg_guesses_update, \
        _green_rate_update, \
        _yellow_rate_update

    def _update_user(self, username:str, win:bool, guesses:int, greens:int, yellows:int, uniques:int, date:int) -> None:

        # initialize cursor
        _cur = self._database.cursor()

        # get fields needed calculate stats for this user
        _raw = _cur.execute(f"SELECT games, wins, guesses, greens, yellows, uniques, guess_distro, last_solve, curr_streak FROM User_Data WHERE username = '{username}';").fetchone()
        
        # get update values for wins, streak, last_solve, and guess distribution
        _games_update, \
        _wins_update, \
        _guesses_update, \
        _greens_update, \
        _yellows_update, \
        _uniques_update, \
        _last_solve_update, \
        _streak_update, \
        _distro_str_update, \
        _win_rate_update, \
        _avg_guesses_update, \
        _green_rate_update, \
        _yellow_rate_update = self._get_update_values(_raw, win, guesses, greens, yellows, uniques, date)

        # execute sql script to update data in database for this user
        _cur.executescript(f'''
            UPDATE User_Data SET games = {_games_update} WHERE username = '{username}';
            UPDATE User_Data SET wins = {_wins_update} WHERE username = '{username}';
            UPDATE User_Data SET guesses = {_guesses_update} WHERE username = '{username}';
            UPDATE User_Data SET greens = {_greens_update} WHERE username = '{username}';
            UPDATE User_Data SET yellows = {_yellows_update} WHERE username = '{username}';
            UPDATE User_Data SET uniques = {_uniques_update} WHERE username = '{username}';
            UPDATE User_Data SET guess_distro = '{_distro_str_update}' WHERE username = '{username}';
            UPDATE User_Data SET last_solve = {_last_solve_update} WHERE username = '{username}';
            UPDATE User_Data SET curr_streak = {_streak_update} WHERE username = '{username}';
            UPDATE User_Data SET last_submit = {date} WHERE username = '{username}';

            UPDATE User_Stats SET win_rate = {_win_rate_update} WHERE username = '{username}';
            UPDATE User_Stats SET avg_guesses = {_avg_guesses_update} WHERE username = '{username}';
            UPDATE User_Stats SET green_rate = {_green_rate_update} WHERE username = '{username}';
            UPDATE User_Stats SET yellow_rate = {_yellow_rate_update} WHERE username = '{username}';''')

        # close cursor
        _cur.close()

        # commit changes to the database
        self._database.commit()


    def _add_user(self, username:str, win:bool, guesses:int, greens:int, yellows:int, uniques:int, date:int) -> None:
        
        # initialize the distribution dictionary
        _distro_dict = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

        # set guess distribution if the player won
        if win:
            _distro_dict[guesses] += 1

        # convert dictionary to string
        _distro_insert = ' '.join(map(str, _distro_dict.values()))

        # attempts set to 1
        _games_insert = 1
        
        # solves and streak set to 1 if solved; otherwise 0
        _wins_insert = _streak_insert = 1 if win else 0

        # last_solve will set to todays date if solved; otherwise set to 0
        _date_insert = date if win else 0

        # calculate the win_rate
        _win_rate = _wins_insert 

        # get number of guesses
        _avg_guesses = guesses

        # get the green rate
        _green_rate = greens / uniques

        # get the yellow rate
        _yellow_rate = yellows / uniques

        # initialize cursor
        _cur = self._database.cursor()

        # execute sql script to add new user to the database
        _cur.executescript(f'''
            INSERT INTO User_Data (
                username, 
                games, 
                wins, 
                guesses, 
                greens, 
                yellows,
                uniques, 
                guess_distro,
                last_solve,
                last_submit,
                curr_streak, 
                max_streak) 
                Values (
                    '{username}', 
                    {_games_insert}, 
                    {_wins_insert}, 
                    {guesses}, 
                    {greens}, 
                    {yellows}, 
                    {uniques},
                    '{_distro_insert}',
                    {_date_insert},
                    {date},
                    {_streak_insert}, 
                    {_streak_insert});

            INSERT INTO User_Stats (
                username, 
                win_rate, 
                avg_guesses, 
                green_rate, 
                yellow_rate)
                Values (
                    '{username}', 
                    {_win_rate}, 
                    {_avg_guesses}, 
                    {_green_rate}, 
                    {_yellow_rate});''')

        # close the cursor
        _cur.close()

        # commit the changes to the database
        self._database.commit()

        print('changes_committed')

        # return the base_stats

    def submit_data(self, username:str, dtime:datetime, win:bool, guesses:int, greens:int, yellows:int, uniques:int) -> None:
        '''Given the username and info on attempt, user stats are updated in the database. A user is added to the database if
        they are a new user. Method will raise DoubleSubmit exception if method is called on the same user twice or more on one day'''

        # convert datetime object to int of form YYYYMMDD
        _date = int(dtime.strftime('%Y%m%d'))

        # initialize cursor
        _cur = self._database.cursor()

        # get the raw result from the database query. _raw will be a tuple containing the last solve for the specified username if they are in 
        # the database. _raw will be None if the username does not exist in the database
        _raw = _cur.execute(f"SELECT last_submit from User_Data WHERE username = '{username}';").fetchone()

        # close the cursor
        _cur.close()

        # user does exist in database
        if _raw:
            # extract the last submission date for this user
            _last_submit, = _raw

            # check if this user has already submitted this day
            if _last_submit == _date and not DEBUG:

                # raise DoubleSubmit exception
                raise DoubleSubmit(username)
            
            # if we get to this point the user is submitting for the first time on day: _date
            # update stats
            self._update_user(username, win, guesses, greens, yellows, uniques, _date)

        # user does not exist in database
        else:
            # add the user to the database
            self._add_user(username, win, guesses, greens, yellows, uniques, _date)