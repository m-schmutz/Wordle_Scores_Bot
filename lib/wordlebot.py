# base python modules
from datetime import datetime
from enum import Enum, auto
from collections import Counter
from time import perf_counter
from dataclasses import dataclass
from random import choice

# pip modules
import cv2
import numpy as np
import discord
from discord import Intents, Object, ButtonStyle
from discord.ui import Button, View
from discord.ext import commands
from pytesseract import image_to_string

# import local modules
import ansi
from botdatabase import *
from scraper import WOTDScraper
from wordlookup import WordLookup
from wordinfo import WordInfo



def timer(func):
    def _inner(*args, **kwargs):
        beg = perf_counter()
        ret = func(*args, **kwargs)
        end = perf_counter()
        print(ansi.magenta(f'[{end-beg:.06f}]: {func.__name__}'))
        return ret
    return _inner

### Descriptor/Lightweight Classes


class InvalidGame(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)
        self.message = message


################################################################################################################################################
# Score class:
# lol idk
################################################################################################################################################
class Score(Enum):
    CORRECT = auto()
    MISPLACED = auto()
    INCORRECT = auto()

    def __repr__(self) -> str:
        match self:
            case Score.CORRECT:
                return ansi.green(self.name[0])
            case Score.MISPLACED:
                return ansi.yellow(self.name[0])
            case Score.INCORRECT:
                return ansi.bright_black(self.name[0])

        raise AssertionError(f'Unexpected Score "{self.name}"')

################################################################################################################################################
# SubmissionEmbed class:
# used to display a users results after a game
################################################################################################################################################
class SubmissionEmbed(discord.Embed):
    def __init__(self, username: str, stats: BaseStats):
        super().__init__(
            color= discord.Color.random(),
            title= f'Results for **{username}**',
            description= None,
            timestamp= None)

        # self.set_image(url='https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fimgc.allpostersimages.com%2Fimg%2Fposters%2Fsteve-buscemi-smiling-in-close-up-portrait_u-L-Q1171600.jpg%3Fh%3D550%26p%3D0%26w%3D550%26background%3Dffffff&f=1&nofb=1')
        self.add_field(name='Guess Distribution', value=stats.guess_distro, inline=False
            ).add_field(name='Games Played', value=stats.games_played, inline=False
            ).add_field(name='Win Rate', value=f'{stats.win_rate:.02f}%', inline=False
            ).add_field(name='Streak', value=stats.streak, inline=False
            ).add_field(name='Max Streak', value=stats.max_streak, inline=False)

################################################################################################################################################
# LinkView class:
# used to display the wordle website in discord
################################################################################################################################################
class LinkView(View):
    def __init__(self):
        super().__init__(timeout=0)
        self.add_item(Button(
            label= 'Play Wordle',
            style= ButtonStyle.link,
            url= 'https://www.nytimes.com/games/wordle/index.html'))

################################################################################################################################################
# GameStats class:
# used to store stats of a submitted game
################################################################################################################################################
@dataclass
class GameStats:
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

################################################################################################################################################
# WordleBot class:
# Driver code for the Wordle Bot
################################################################################################################################################
class WordleBot(commands.Bot):
    def __init__(self, server_id: int) -> None:
        super().__init__(
            command_prefix= '!',
            intents= Intents.all(),
            help_command= None)
        self._tessConfig = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self._maxThresh = 255 # maximum pixel value
        self._darkThresh = 0x26 # midpoint between the BG and the next darkest color
        self._lightThresh = 0xeb # midpoint between the BG and the next brightest color
        self.synced = False
        self.guild = Object(id=server_id)
        self.scraper = WOTDScraper()
        self.db = BotDatabase(db_path='./lib/bot_database/stats.db')

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

    def scoreGame(self, image: bytes, submissionDate: datetime) -> GameStats:
        """Parse a screenshot of a Wordle game and return a GameStats object containing
        information about the results.
        
        ---
        ## Parameters

        image : `bytes`
            The user-provided screenshot of their Wordle game.

        submissionDate : `datetime`
            A datetime object respresenting the time of submission.

        ---
        ## Returns

        object : `GameStats`
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
        scores = np.full(shape=guesses.shape, fill_value=Score.INCORRECT)
        uniques = [set() for _ in range(5)]
        tC = tM = uC = uM = 0
        for row, guess in enumerate(guesses):
            _counts = counts.copy()
            remaining = []

            # score CORRECT LETTERS in CORRECT POSITION (Green)
            for col, gc, wc in zip(range(5), guess, wotd):
                if gc == wc:
                    scores[row,col] = Score.CORRECT
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
                    scores[row,col] = Score.MISPLACED
                    _counts[gc] -= 1
                    tM += 1
                    if gc not in uniques[col]:
                        uM += 1

                #(2/2) ...finish adding unique chars
                uniques[col].add(gc)

        return GameStats(
            guessTable= guesses,
            numGuesses= guesses.shape[0],
            solution= wotd,
            won= all(s == Score.CORRECT for s in scores[-1]),
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
