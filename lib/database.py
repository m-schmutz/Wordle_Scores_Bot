import sqlite3 as sql
from datetime import datetime
from os import path

LTRS_IN_GUESS = 5

# set DEBUG to True if you want to ignore double submits
DEBUG = False

class BaseStats:
    """Default statistics to return upon a submission.

    ---
    - \# guesses distribution
    - \# games played
    - win %
    - streak
    - max streak"""
    def __init__(self, guessDistribution: str, numGamesPlayed: int, winRate: float, streak: int, maxStreak: int) -> None:
        self.guessDistribution = str(guessDistribution)
        self.numGamesPlayed = int(numGamesPlayed)
        self.winRate = float(winRate)
        self.streak = int(streak)
        self.maxStreak = int(maxStreak)

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
        
class GroupStats:
    '''
    Object to contain group stats returned from the database

    ---
    #### Members
    - attempts
    - solves
    - guesses
    - greens
    - yellows
    - total_letters
    - avg_guesses
    - green_rate
    - yellow_rate
    '''
    def __init__(self, __raw:tuple):
        attempts, solves, guesses, greens, yellows = __raw

        self.attempts = attempts
        self.solves = solves 
        self.guesses = guesses
        self.greens = greens
        self.yellows = yellows

        _total_letters = guesses * LTRS_IN_GUESS
        self.total_letters = _total_letters

        self.avg_guesses = guesses / attempts

        self.green_rate = (greens / _total_letters) * 100
        self.yellow_rate = (yellows / _total_letters) * 100

    def __str__(self) -> str:
        return f'''
        group attempts = {self.attempts}
        group solves = {self.solves}
        group guesses = {self.guesses}
        group average guesses = {self.avg_guesses}
        group greens = {self.greens}
        group yellows = {self.yellows}
        group total letters = {self.total_letters}
        group green rate = {self.green_rate}
        group yellow rate = {self.yellow_rate}
        '''

class DoubleSubmit(Exception):
    '''Exception raised if user attempts to submit twice on the same day'''
    
    # takes in username to print out whihc user is attempting to submit twice 
    def __init__(self, username) -> None:
        self.username = username    
        self.message = 'You already submit today\'s game :)'

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
                username varchar(32), 
                attempts int, 
                solves int, 
                guesses int, 
                greens int, 
                yellows int, 
                curr_streak int, 
                max_streak int, 
                last_solve int, 
                last_submit int,
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

    def get_group_stats(self) -> GroupStats:

        # initialize cursor
        _cur = self._database.cursor()

        # get group data from the database
        _raw = _cur.execute('SELECT * FROM Group_Data').fetchone()
        
        # close cursor
        _cur.close()

        # initialize GroupStats object with values from database
        group_stats = GroupStats(_raw)

        # return the GroupData object
        return group_stats

    def _get_update_values(self, solved:int, _last_solve:int, date:int):
        # increase solves if user solved the wordle; otherwise solves stays the same
        _solves_update = 'solves + 1' if solved else 'solves'

        # increment streak if user has solved consecutively; otherwise streak will not be incremented
        _continue_streak = (date - _last_solve) == 1 

        # last solve is set to current date if wordle solved; otherwise last solve stays the same
        _last_solve_update = date if solved else _last_solve

        # increment streak 
        if solved and _continue_streak:
            _streak_update = 'curr_streak + 1'
        
        # set streak to 1 if this is the start of a new streak
        elif solved:
            _streak_update = '1'

        # set streka to 0 if user did not solve wordle today
        else:
            _streak_update = '0'

        # return computed values
        return _solves_update, _streak_update, _last_solve_update

    def _update_user(self, username:str, solved:bool, guesses:int, greens:int, yellows:int, date:int) -> None:

        # initialize cursor
        _cur = self._database.cursor()

        # get the last solve date for this user
        _last_solve, = _cur.execute(f"SELECT last_solve FROM User_Data WHERE username = '{username}';").fetchone()

        # get the update values for the database
        _solves_update, _streak_update, _last_solve_update = self._get_update_values(solved, _last_solve, date)
        
        # execute sql script to update data in database for this user
        _cur.executescript(f'''
            UPDATE User_Data SET attempts = attempts + 1 WHERE username = '{username}';
            UPDATE User_Data SET solves = {_solves_update} WHERE username = '{username}';
            UPDATE User_Data SET guesses = guesses + {guesses} WHERE username = '{username}';
            UPDATE User_Data SET greens = greens + {greens} WHERE username = '{username}';
            UPDATE User_Data SET yellows = yellows + {yellows} WHERE username = '{username}';
            UPDATE User_Data SET curr_streak = {_streak_update} WHERE username = '{username}';
            UPDATE User_Data SET last_solve = {_last_solve_update} WHERE username = '{username}'; 
            UPDATE User_Data SET last_submit = {date} WHERE username = '{username}';

            UPDATE Group_Data SET attempts = attempts + 1;
            UPDATE Group_Data SET solves = {_solves_update};
            UPDATE Group_Data SET guesses = guesses + {guesses};
            UPDATE Group_Data SET greens = greens + {greens};
            UPDATE Group_Data SET yellows = yellows + {yellows};
        ''')

        # close cursor
        _cur.close()

        # commit changes to the database
        self._database.commit()

    def _add_user(self, username:str, solved:bool, guesses:int, greens:int, yellows:int, date:int) -> None:
        
        # attempts set to 1
        _attempts_insert = 1
        
        # solves and streak set to 1 if solved; otherwise 0
        _solves_insert = _streak_insert = 1 if solved else 0

        # last_solve will set to todays date if solved; otherwise set to 0
        _date_insert = date if solved else 0
       
        # initialize cursor
        _cur = self._database.cursor()

        # execute sql script to add new user to the database
        _cur.executescript(f'''
            INSERT INTO User_Data (
                username, 
                attempts, 
                solves, 
                guesses, 
                greens, 
                yellows, 
                curr_streak, 
                max_streak, 
                last_solve,
                last_submit)
                Values (
                    '{username}', 
                    {_attempts_insert}, 
                    {_solves_insert}, 
                    {guesses}, 
                    {greens}, 
                    {yellows}, 
                    {_streak_insert}, 
                    {_streak_insert}, 
                    {_date_insert},
                    {date});

            UPDATE Group_Data SET attempts = attempts + 1;
            UPDATE Group_Data SET solves = solves + {_solves_insert};
            UPDATE Group_Data SET guesses = guesses + {guesses};
            UPDATE Group_Data SET greens = greens + {greens};
            UPDATE Group_Data SET yellows = yellows + {yellows};
        ''')

        # close the cursor
        _cur.close()

        # commit the changes to the database
        self._database.commit()

    def submit_data(self, username:str, dtime:datetime, solved:bool, guesses:int, greens:int, yellows:int) -> BaseStats:
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
            self._update_user(username, solved, guesses, greens, yellows, _date)

        # user does not exist in database
        else:
            # add the user to the database
            self._add_user(username, solved, guesses, greens, yellows, _date)
        

        guessDistr = '10 20 30 40 50 60'
        numGames = 32
        winPerc = 94.342341
        streak = 3
        maxStreak = 8
        return BaseStats(guessDistr, numGames, winPerc, streak, maxStreak)
