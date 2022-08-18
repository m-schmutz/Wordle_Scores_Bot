import sqlite3 as sql
from datetime import datetime
from os import path
from typing import Tuple

LTRS_IN_GUESS = 5

# set DEBUG to True if you want to ignore double submits
DEBUG = False

class BaseStats:
    """Default statistics to return upon a submission.

    ---
    - guesses distribution
    - \# games played
    - win %
    - streak
    - max streak"""
    def __init__(self, distro_str:str, games_played:int, win_rate:float, streak:int, max_streak:int) -> None:
        self.guess_distro = str(distro_str)
        self.games_played = int(games_played)
        self.win_rate = float(win_rate)
        self.streak = int(streak)
        self.max_streak = int(max_streak)
        
class FullStats(BaseStats):
    '''FullStats for a user
    
    ---
    - \# games played
    - \# total wins
    - \# total guesses
    - \# total greens
    - \# total yellows
    - \# uniques
    - guesses distribution
    - current streak
    - max streak
    - win rate
    - average \# of guesses
    - green rate 
    - yellow rate
    '''
    def __init__(self, raw:Tuple) -> None:

        # extract data fields from tuple
        games_played, \
        total_wins, \
        total_guesses, \
        total_greens, \
        total_yellows, \
        uniques, \
        distro_str, \
        streak, \
        max_streak, \
        win_rate, \
        avg_guesses, \
        green_rate, \
        yellow_rate = raw

        # initialize BaseStats members
        super().__init__(distro_str, games_played, win_rate, streak, max_streak)

        # initialize the FullStats fields
        self.total_wins = int(total_wins)
        self.total_guesses = int(total_guesses)
        self.total_greens = int(total_greens)
        self.total_yellows = int(total_yellows)
        self.uniques = int(uniques)
        self.avg_guesses = float(avg_guesses)
        self.green_rate = float(green_rate)
        self.yellow_rate = float(yellow_rate)
        
class UpdateValues:
    def __init__(self, raw:Tuple, win:bool, guesses:int, greens:int, yellows:int, uniques:int, date:int) -> None:
        
        # extract fields from tuple
        _games, _wins, _guesses, _greens, _yellows, _uniques, _distro_str, _last_solve, _curr_streak, _max_streak = raw


        # games update value
        self._games_update = _games + 1

        # wins update value
        self._wins_update = _wins + win

        # guesses update value
        self._guesses_update = _guesses + guesses

        # greens update value
        self._greens_update = _greens + greens

        # yellows update value
        self._yellows_update = _yellows + yellows

        # uniques update value
        self._uniques_update = _uniques + uniques

        # increment streak if user has solved consecutively; otherwise streak will not be incremented
        _continue_streak = (date - _last_solve) == 1 

        # last solve is set to current date if wordle solved; otherwise last solve stays the same
        self._last_solve_update = date if win else _last_solve


        # increment streak 
        if win and _continue_streak:
            self._streak_update = _curr_streak + 1
        
        # set streak to 1 if this is the start of a new streak
        elif win:
            self._streak_update = 1

        # set streka to 0 if user did not solve wordle today
        else:
            self._streak_update = 0


        # set max streak accordingly
        self._max_update = self._streak_update if self._streak_update > _max_streak else _max_streak


        # if they win, update the guess distribution
        if win:
            # convert string to dictionary
            temp_dict = dict( (k,v) for k,v in zip(range(1,7), map(int, _distro_str.split())))

            # update dictionary
            temp_dict[guesses] += 1

            # convert dictionary back to string
            self._distro_str_update = ' '.join(map(str, temp_dict.values()))
            
        # otherwise it stays the same
        else:
            self._distro_str_update = _distro_str


        # win rate update value
        self._win_rate_update = self._wins_update / self._games_update

        # avg guesses update value
        self._avg_guesses_update = self._guesses_update / self._games_update

        # green rate update value
        self._green_rate_update = self._greens_update / self._uniques_update

        # yellow rate update value 
        self._yellow_rate_update = self._yellows_update / self._uniques_update

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
                );''')
            
            # close the cursor
            _cur.close()

        # commit the changes to the database
        self._database.commit()

    def __del__(self) -> None:
        # close connection to database
        self._database.close()

    def _update_user(self, username:str, win:bool, guesses:int, greens:int, yellows:int, uniques:int, date:int) -> BaseStats:

        # initialize cursor
        _cur = self._database.cursor()

        # get fields needed calculate stats for this user
        _raw = _cur.execute(f'''SELECT games, 
                                       wins, 
                                       guesses, 
                                       greens, 
                                       yellows, 
                                       uniques, 
                                       guess_distro, 
                                       last_solve, 
                                       curr_streak, 
                                       max_streak FROM User_Data WHERE username = '{username}';''').fetchone()
                
        # create update values object
        vals = UpdateValues(_raw, win, guesses, greens, yellows, uniques, date)

        # execute sql script to update data in database for this user
        _cur.executescript(f'''
            UPDATE User_Data SET games = {vals._games_update} WHERE username = '{username}';
            UPDATE User_Data SET wins = {vals._wins_update} WHERE username = '{username}';
            UPDATE User_Data SET guesses = {vals._guesses_update} WHERE username = '{username}';
            UPDATE User_Data SET greens = {vals._greens_update} WHERE username = '{username}';
            UPDATE User_Data SET yellows = {vals._yellows_update} WHERE username = '{username}';
            UPDATE User_Data SET uniques = {vals._uniques_update} WHERE username = '{username}';
            UPDATE User_Data SET guess_distro = '{vals._distro_str_update}' WHERE username = '{username}';
            UPDATE User_Data SET last_solve = {vals._last_solve_update} WHERE username = '{username}';
            UPDATE User_Data SET curr_streak = {vals._streak_update} WHERE username = '{username}';
            UPDATE User_Data SET max_streak = {vals._max_update} WHERE username = '{username}';
            UPDATE User_Data SET last_submit = {date} WHERE username = '{username}';

            UPDATE User_Stats SET win_rate = {vals._win_rate_update} WHERE username = '{username}';
            UPDATE User_Stats SET avg_guesses = {vals._avg_guesses_update} WHERE username = '{username}';
            UPDATE User_Stats SET green_rate = {vals._green_rate_update} WHERE username = '{username}';
            UPDATE User_Stats SET yellow_rate = {vals._yellow_rate_update} WHERE username = '{username}';''')

        # close cursor
        _cur.close()

        # commit changes to the database
        self._database.commit()

        # return the stats object
        return BaseStats(vals._distro_str_update, vals._games_update, vals._win_rate_update, vals._streak_update, vals._max_update)

    def _add_user(self, username:str, win:bool, guesses:int, greens:int, yellows:int, uniques:int, date:int) -> BaseStats:
        
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

        # return the base_stats
        return BaseStats(_distro_insert, _games_insert, _win_rate, _streak_insert, _streak_insert)

    def submit_data(self, username:str, dtime:datetime, win:bool, guesses:int, greens:int, yellows:int, uniques:int) -> BaseStats:
        '''Given the username and info on game submission, user stats are updated in the database and their BaseStats are returned. A user is added to the database if
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
            return self._update_user(username, win, guesses, greens, yellows, uniques, _date)

        # user does not exist in database
        else:
            # add the user to the database
            return self._add_user(username, win, guesses, greens, yellows, uniques, _date)

    def get_full_stats(self, username:str) -> FullStats:
        
        # initialize cursor
        _cur = self._database.cursor()

        # get all data fields for the specified user
        _raw = _cur.execute(f'''SELECT games, 
                                       wins,
                                       guesses, 
                                       greens, 
                                       yellows, 
                                       uniques, 
                                       guess_distro,
                                       curr_streak, 
                                       max_streak,
                                       win_rate, 
                                       avg_guesses,
                                       green_rate, 
                                       yellow_rate FROM User_Data CROSS JOIN User_Stats WHERE User_Data.username = '{username}';''').fetchone()
        
        # return FullStats object
        return FullStats(_raw)