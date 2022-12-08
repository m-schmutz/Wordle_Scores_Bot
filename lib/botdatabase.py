from sqlite3 import connect
from os.path import exists
from datetime import datetime
from dataclasses import dataclass
from atexit import register
from typing import Tuple

# objects needed by wordle bot
__all__ = ['BaseStats', 'FullStats', 'BotDatabase']

# set DBLSUB_DISABLED to True if you want to ignore double submits
DBLSUB_DISABLED = False

# path to the database
DB_PATH = './lib/bot_database/stats.db'


################################################################################################################################################
# BaseStats class:
# used to store a user's base stats
################################################################################################################################################
@dataclass
class BaseStats:
    """
    Default statistics to return upon a submission.
    
    ---
    - guesses distribution
    - \# games played
    - win %
    - streak
    - max streak"""

    guess_distro: str | dict
    games_played: int
    win_rate: float
    streak: int
    max_streak: int

    def __post_init__(self):
        # multiply win_rate to convert to %
        self.win_rate *= 100

        # Convert guess distribution from str to dict
        # self.guess_distro = {
        #     k: v
        #     for k,v in zip(
        #         range(1,7),
        #         map(int, self.guess_distro.split())) }

        self.WHOLE = '█'
        self.HALF = '▌'

        farb = {
            1: self.HALF,
            2: self.WHOLE,
            3: self.WHOLE + self.HALF,
            4: self.WHOLE * 2,
            5: self.WHOLE * 2 + self.HALF,
            6: self.WHOLE * 3
        }

        asdf = ''
        for i, v in enumerate(farb.values()):
            asdf += '`' + str(i+1) + ':' + v + '`\n'
        self.guess_distro = f'{asdf}'

################################################################################################################################################
# FullStats class:
# used to store a user's full stats
################################################################################################################################################
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
    - last_win
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
        last_win, \
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
        self.green_rate = float(green_rate) * 100
        self.yellow_rate = float(yellow_rate) * 100
        self.last_win = datetime.strptime(str(last_win), '%Y%m%d').date()

################################################################################################################################################
# Updatevalues class:
# used to update a user's stats for the database
################################################################################################################################################
class UpdateValues:
    def __init__(self, raw:Tuple, win:bool, guesses:int, greens:int, yellows:int, uniques:int, date:int) -> None:
        
        # extract fields from tuple
        _games, _wins, _guesses, _greens, _yellows, _uniques, _distro_str, _last_win, _curr_streak, _max_streak = raw


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

        # last solve is set to current date if wordle solved; otherwise last solve stays the same
        self._last_win_update = date if win else _last_win



        # increment streak if user has solved consecutively; otherwise streak will not be incremented
        # else set streak to 1 if this is the start of a new streak
        if win:
            if date - _last_win == 1:
                self._streak_update = _curr_streak + 1
            else:
                self._streak_update = 1

        # set streak to 0 if user did not solve wordle today
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

################################################################################################################################################
# BotDatabase class:
# used to access and manipulate data in the wordle bot database
################################################################################################################################################
class BotDatabase:
    '''Database class. Contains one member _database. 
    _database is a sqlite3 database connection where data is stored.
    '''
    def submit_data(self, username:str, dtime:datetime, win:bool, guesses:int, greens:int, yellows:int, uniques:int) -> Tuple[BaseStats|None,str]:
        '''Given the username and info on game submission, user stats are updated in the database and their BaseStats are returned. 
        A user is added to the database if they are a new user. 
        Method will raise DoubleSubmit exception if method is called on the same user twice or more on one day'''

        return None, 'DoubleSubmit'

    
        