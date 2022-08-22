import cv2
import numpy as np
import discord
from discord import Intents, Object
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from pytesseract import image_to_string

from datetime import datetime
from enum import Enum, auto
from collections import Counter
from typing import Tuple
from time import perf_counter
from dataclasses import dataclass
from sqlite3 import connect
from random import choice
from os import path

import ansi



def timer(func):
    def _inner(*args, **kwargs):
        beg = perf_counter()
        ret = func(*args, **kwargs)
        end = perf_counter()
        print(ansi.magenta(f'[{end-beg:.06f}]: {func.__name__}'))
        return ret
    return _inner



# set DBLSUB_ENABLED to True if you want to ignore double submits
DBLSUB_ENABLED = False

class BaseStats:
    """Default statistics to return upon a submission.

    ---
    - guesses distribution
    - \# games played
    - win %
    - streak
    - max streak"""
    def __init__(self, distro_str:str, games_played:int, win_rate:float, streak:int, max_streak:int) -> None:
        self.guess_distro = dict( (k,v) for k,v in zip(range(1,7), map(int, distro_str.split())))
        self.games_played = int(games_played)
        self.win_rate = float(win_rate) * 100
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

        # increment streak if user has solved consecutively; otherwise streak will not be incremented
        _continue_streak = (date - _last_win) == 1 

        # last solve is set to current date if wordle solved; otherwise last solve stays the same
        self._last_win_update = date if win else _last_win


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
        self.message = 'You already submit today\'s game :)'

    # set __module__ to exception module (nice print out message)
    ## this can be taken out later
    __module__ = Exception.__module__
    
    # print string including username of user that has attempted to submit twice
    def __str__(self):
        return f'{self.username} has already submitted today'

class BotDatabase:
    '''Database class. Contains one member _database. 
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
        self._database = connect(db_path)

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
                last_win int, 
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

        # get fields needed calculate updated stats for this user
        _raw = _cur.execute(f'''SELECT games, 
                                       wins, 
                                       guesses, 
                                       greens, 
                                       yellows, 
                                       uniques, 
                                       guess_distro, 
                                       last_win, 
                                       curr_streak, 
                                       max_streak FROM User_Data WHERE username = '{username}';''').fetchone()
                
        # create update values object. This will calculate all the updated stats
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
            UPDATE User_Data SET last_win = {vals._last_win_update} WHERE username = '{username}';
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
                last_win,
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
        '''Given the username and info on game submission, user stats are updated in the database and their BaseStats are returned. 
        A user is added to the database if they are a new user. 
        Method will raise DoubleSubmit exception if method is called on the same user twice or more on one day'''

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
            if _last_submit == _date and not DBLSUB_ENABLED:

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
                                       last_win,
                                       curr_streak, 
                                       max_streak,
                                       win_rate, 
                                       avg_guesses,
                                       green_rate, 
                                       yellow_rate FROM User_Data CROSS JOIN User_Stats WHERE User_Data.username = '{username}';''').fetchone()
        
        # close the cursor
        _cur.close()

        # return FullStats object
        return FullStats(_raw)



@dataclass
class WordleGame:
    """Game stats DTO"""

    guessTable: np.ndarray
    numGuesses: int
    solution: str
    won: bool
    uniqueCorrect: int
    uniqueMisplaced: int
    uniqueAll: int
    totalCorrect: int
    totalMisplaced: int

class InvalidGame(Exception):
    def __init__(self, reason: str, *args: object) -> None:
        super().__init__(*args)
        self.reason = reason

class CharScore(Enum):
    CORRECT = auto()
    MISPLACED = auto()
    INCORRECT = auto()

    def __repr__(self) -> str:
        match self:
            case CharScore.CORRECT:
                return ansi.green(self.name[0])
            case CharScore.MISPLACED:
                return ansi.yellow(self.name[0])
            case CharScore.INCORRECT:
                return ansi.bright_black(self.name[0])

        raise AssertionError(f'Unexpected CharScore "{self.name}"')

class SubmissionReply(discord.Embed):
    def __init__(self, username: str, stats: BaseStats):
        super().__init__(
            color= discord.Color.random(),
            title= f'>>> Results for {username}',
            description= None,
            timestamp= None)

        # self.set_image(url='https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fimgc.allpostersimages.com%2Fimg%2Fposters%2Fsteve-buscemi-smiling-in-close-up-portrait_u-L-Q1171600.jpg%3Fh%3D550%26p%3D0%26w%3D550%26background%3Dffffff&f=1&nofb=1')
        self.add_field(name='Guess Distribution', value=stats.guess_distro, inline=False)
        self.add_field(name='Games Played', value=stats.games_played, inline=False)
        self.add_field(name='Win Rate', value=f'{stats.win_rate:.02f}%', inline=False)
        self.add_field(name='Streak', value=stats.streak, inline=False)
        self.add_field(name='Max Streak', value=stats.max_streak, inline=False)

class WordleScraper:
    """Keeps track of the Word of the Day. Uses Selenium to scrape the NYTimes Wordle webpage."""

    def __init__(self) -> None:
        opts = webdriver.FirefoxOptions()
        opts.headless = True
        opts.page_load_strategy = 'eager'
        serv = Service(log_path='./lib/geckodriver.log')

        self._driver = webdriver.Firefox(options=opts, service=serv)
        self._url = 'https://www.nytimes.com/games/wordle/index.html'
        self._localStorageScript = 'return JSON.parse(this.localStorage.getItem("nyt-wordle-state")).solution'
        self._last_updated = datetime.now().date()
        self._wotd = self._getWotd()

    def __del__(self) -> None:
        # WILL CAUSE MEMORY LEAK IF NOT CLOSED
        self._driver.quit()

    def _getWotd(self) -> str:
        """Webscrapes the official webpage to obtain the Word of the Day."""

        self._driver.get(self._url)
        return str(self._driver.execute_script(self._localStorageScript))

    def wotd(self, date: datetime) -> str:
        """Returns today's word."""

        # Potentially update today's word
        today = datetime.now().date()
        if self._last_updated < today:
            prev_wotd = self._wotd
            self._wotd = self._getWotd()
            self._last_updated = today

            # If we updated the word as user submit, return the previous word
            if date < today:
                return prev_wotd

        return self._wotd



class WordleBot(commands.Bot):
    def __init__(self, server_id: int) -> None:
        super().__init__(
            command_prefix= '!',
            intents= Intents.all(),
            help_command= None)
        self._tessConfig = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self._maxThresh = 255
        self._darkThresh = 0x26
        self._lightThresh = 0xeb
        # Dark Theme:
        #   BG = 0x121213 (0x12 grayscale)
        #   Next darkest = 0x3a3a3c (0x3a grayscale)
        #   => midpoint = 0x26
        # Light Theme:
        #   BG = 0xffffff (0xff grayscale)
        #   Next lightest = 0xd3d6da (0xd6 grayscale)
        #   => midpoint = 0xeb

        self.synced = False
        self.guild = Object(id=server_id)
        self.scraper = WordleScraper()
        self.db = BotDatabase(db_path='./lib/stats.db')

    def _guessesFromImage(self, image: bytes) -> np.ndarray:
        """Use Tesseract to compile a list of the guesses.
        
        ---
        ## Parameters

        image : `bytes`
            The user-provided screenshot of their Wordle game.

        ---
        ## Returns

        object : `np.ndarry`
            A 2-D array of the words within the image.

        ---
        ## Raises

        InvalidGame
            Unable to find a game in the image."""

        ### Get cell contours ###

        # Convert image (bytes) to OpenCV matrix (cv2.Mat) and get grayscale
        mat = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)

        # Create a mask of the character cells so we can find their contours
        if np.median(gray[:1,:]) < 200: # Dark theme
            _, cellmask = cv2.threshold(gray, self._darkThresh, self._maxThresh, cv2.THRESH_BINARY)
        else: # Light theme
            _, cellmask = cv2.threshold(gray, self._lightThresh, self._maxThresh, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(cellmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Discard as many unreasonable contours as possible
        filtered = []
        for c in contours:
            # Skip non-quadrilaterals
            if c.shape != (4,1,2):
                continue
            
            # Skip ~non-squares
            _,_,w,h = cv2.boundingRect(c)
            if abs(w-h) > (w+h)*0.015:
                continue

            filtered.append(c)

        # Remove all axis of length one since they are useless
        cell_contours = np.squeeze(filtered)
        if len(cell_contours) != 30:
            raise InvalidGame('Could not find the game!')
        _, charmask = cv2.threshold(gray, self._lightThresh, self._maxThresh, cv2.THRESH_BINARY_INV)

        ### Transform charmask to increase legibility ###

        # squeeze letters horizontally in reverse order since cv2.findContours works
        # from SE to NW and we want our contours organized from NW to SE (i.e. guess order).
        cols = []
        for c in cell_contours[:5]:
            x,_,w,_ = cv2.boundingRect(c)
            off = w // 4
            cols.append(charmask[:, x+off : x+w-off])
        charmask = cv2.hconcat(cols[::-1])

        # crop vertically
        ys = set(y
            for contour in cell_contours
            for (_, y) in contour)
        charmask = charmask[min(ys):max(ys), :]

        ### Get dem words ###

        # Generate mask and feed Tesseract :) *pat* *pat* good boy
        text:str = image_to_string(image=charmask, lang="eng", config=self._tessConfig)
        guess_list = text.strip().lower().split('\n')

        # Validate guesses
        from word_lookup import WordLookup
        valid_words = set(WordLookup().get_valid_words())
        for guess in guess_list:
            if guess not in valid_words:
                raise InvalidGame('Invalid word detected!')

        # Return guesses as 2-D numpy array
        return np.array( [list(g) for g in guess_list] )

    def getResponse(self, solved: bool, numGuesses: int) -> str:
        if solved:
            if numGuesses == 1:
                return choice((
                    'Riiiiight. I\'m sure you didn\'t look it up.',
                    'CHEATER!!!!'))

            if numGuesses < 3:
                return choice((
                    'Damn that\'s crazy... I have google too.',
                    'hmmmmmm 🤔🤔'))

            if numGuesses < 5:
                return choice((
                    'Ok?',
                    'Yea',
                    'Cool.',
                    'Yep, that\'s definitely a Wordle game.'))

            return choice((
                f'It took you {numGuesses} guesses? Lmao.',
                'Garbage.',
                'My grandma could do better.'))

        return choice((
            'You suck!',
            'I\'d say better luck next time, but you clearly don\'t have any luck.',
            'Maybe [this](https://freekidsbooks.org/reading-level/children/) can help you.'))

    def scoreGame(self, image: bytes, submissionDate: datetime) -> WordleGame:
        """Parse a screenshot of a Wordle game and return a WordleGame object containing
        information about the results.
        
        ---
        ## Parameters

        image : `bytes`
            The user-provided screenshot of their Wordle game.

        submissionDate : `datetime`
            A datetime object respresenting the time of submission.

        ---
        ## Returns

        object : `WordleGame`
            DTO for easy use of various game stats.
        """

        # Get user guesses and initialize game data, then score the game.
        # It's easier to score yellows after greens as opposed to "inline". Otherwise,
        #   we would have to look ahead for potential greens because green has a higher
        #   precedence and therefore consumes one of the characters counts before any
        #   would-be yellows have the chance.
        guesses = self._guessesFromImage(image)
        wotd = self.scraper.wotd(submissionDate)
        counts = Counter(wotd)
        scores = np.full(shape=guesses.shape, fill_value=CharScore.INCORRECT)
        uniques = [set() for _ in range(5)]
        tC = tM = uC = uM = 0
        for row, guess in enumerate(guesses):
            _counts = counts.copy()
            remaining = []

            # score CORRECT LETTERS in CORRECT POSITION (Green)
            for col, gc, wc in zip(range(5), guess, wotd):
                if gc == wc:
                    scores[row,col] = CharScore.CORRECT
                    _counts[gc] -= 1
                    tC += 1

                    #(1/2) start adding unique chars...
                    if gc not in uniques[col]:
                        uC += 1
                        uniques[col].add(gc)
                else:
                    remaining.append( (row, col, gc) )

            # score CORRECT LETTERS in WRONG POSITION (Yellow)
            for row, col, gc in remaining:
                if gc in wotd and _counts[gc] > 0:
                    scores[row,col] = CharScore.MISPLACED
                    _counts[gc] -= 1
                    tM += 1
                    if gc not in uniques[col]:
                        uM += 1

                #(2/2) ...finish adding unique chars
                uniques[col].add(gc)

        return WordleGame(
            guessTable= guesses,
            numGuesses= guesses.shape[0],
            solution= wotd,
            won= all(s == CharScore.CORRECT for s in scores[-1]),
            uniqueCorrect= uC,
            uniqueMisplaced= uM,
            uniqueAll= sum(len(set) for set in uniques),
            totalCorrect= tC,
            totalMisplaced= tM)

    ### Overridden methods
    async def on_ready(self):

        # Wait for client cache to load
        await self.wait_until_ready()

        # Sync application commands
        if not self.synced:
            await self.tree.sync(guild=self.guild)
            self.synced = True

        print(f'{self.user} ready!')
