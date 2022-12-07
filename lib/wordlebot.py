# base python modules
from datetime import datetime
from enum import Enum, auto
from collections import Counter
from dataclasses import dataclass
from random import choice
from types import TracebackType

# pip modules
from discord import Intents, Object, ButtonStyle, Embed, File, User, Color
from discord.ui import Button, View
from discord.ext import commands
from pytesseract import image_to_string
import numpy as np
import cv2

# import local modules
from botdatabase import *
from wotd import gen_files, get_wotd, get_valid_words
import ansi
from logger import BotLog


################################################################################################################################################
# InvalidGame class:
# Used by the WordleBot class whenever the results cannot be determined.
################################################################################################################################################
class InvalidGame(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)
        self.message = message

################################################################################################################################################
# Score class:
# Used to represent the separate scores of individual letters.
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
class SubmissionEmbed(Embed):
    def __init__(self, date: datetime, user: User, stats: BaseStats, attachment_filename: str):
        super().__init__(
            color= Color.random(),
            description= None,
            timestamp= None)

        # self.set_image(url='https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fimgc.allpostersimages.com%2Fimg%2Fposters%2Fsteve-buscemi-smiling-in-close-up-portrait_u-L-Q1171600.jpg%3Fh%3D550%26p%3D0%26w%3D550%26background%3Dffffff&f=1&nofb=1')
        self.add_field(name='Guess Distribution', value=stats.guess_distro, inline=False
            ).add_field(name='Games Played', value=stats.games_played, inline=False
            ).add_field(name='Win Rate', value=f'{stats.win_rate:.02f}%', inline=False
            ).add_field(name='Streak', value=stats.streak, inline=False
            ).add_field(name='Max Streak', value=stats.max_streak, inline=False
            ).set_image(url=f'attachment://{attachment_filename}'
            # ).set_author(name=user.display_name, icon_url=user.display_avatar.url
            ).set_footer(icon_url=user.display_avatar.url, text=f'{user.display_name}  ∙  {date}'
        )

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

        super().__init__(command_prefix='!', intents=Intents.all(), help_command=None)

        # generate pickle files if needed
        gen_files()

        # Private members / constants
        self._tessConfig = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self._maxThresh = 255       # maximum pixel value
        self._darkThresh = 0x26     # midpoint between the dark theme BG and the next darkest color
        self._lightThresh = 0xeb    # midpoint between the light theme BG and the next brightest color
        self._valid_words = get_valid_words()
        self._responses = {
            0: (r"You suck!",
                r"I'd say better luck next time, but you clearly don't have any luck.",
                r"Maybe [this](https://freekidsbooks.org/reading-level/children/) can help you."),
            1: (r"Riiiiight. I'm sure you didn't look it up.",
                r"@everyone check out how totally real this game was"),
            2: (r"Damn that's crazy, I can google too.",
                r"hmmmmmm 🤔🤔"),
            3: (r"Ok?",
                r"Yea"),
            4: (r"Cool.",
                r"Yep, that's definitely a Wordle game."),
            5: (r"Garbage.",
                r"My grandma could do better."),
            6: (r"Jesus, it took you long enough.",
                r"Bet you were sweating profusely on that last guess.")
        }

        # Public members
        self.synced = False
        self.guild = Object(id=server_id)
        self.db = BotDatabase()

        # log class, keeps track of all events that happen related to the bot
        self.log = BotLog()


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
        gray = cv2.cvtColor(
            src= cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR),
            code= cv2.COLOR_BGR2GRAY)

        # Determine user theme and create a mask of the character cells so we can find their contours
        image_sides = [*gray[:1,:], *gray[-1:,:]]   # Leftmost and rightmost columns of pixels
        if np.median(image_sides) < 200:
            _, cellmask = cv2.threshold(gray, self._darkThresh, self._maxThresh, cv2.THRESH_BINARY)
        else:
            _, cellmask = cv2.threshold(gray, self._lightThresh, self._maxThresh, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(cellmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Discard as many unreasonable contours as possible
        filtered = []
        for c in contours:
            # Skip non-quadrilaterals
            if c.shape != (4,1,2):
                continue
            
            # Skip non-squares (rough estimate)
            _,_,w,h = cv2.boundingRect(c)
            if abs(w-h) > (w+h)*0.015:
                continue

            filtered.append(c)

        # Remove all axis of length one since they are useless
        cell_contours = np.squeeze(filtered)

        if len(cell_contours) != 30:
            raise InvalidGame('Could not find the game!')
        
        # Generate a mask of the characters
        _, charmask = cv2.threshold(gray, self._lightThresh, self._maxThresh, cv2.THRESH_BINARY_INV)


        ### Transform charmask to increase legibility ###

        # squeeze letters closer horizontally in reverse order since cv2.findContours works
        # from SE to NW and we want our contours organized from NW to SE (i.e. guess order).
        cols = []
        for c in cell_contours[:5]:
            x,_,w,_ = cv2.boundingRect(c)
            off = w // 4
            cols.append(charmask[:, x+off : x+w-off])
        charmask = cv2.hconcat(cols[::-1])

        # trim top and bottom edges of image
        ys = set(
            y
            for contour in cell_contours
            for (_, y) in contour)
        charmask = charmask[min(ys):max(ys), :]


        ### Get dem words ###

        # Generate mask and feed Tesseract :) *pat* *pat* good boy
        text = image_to_string(image=charmask, lang='eng', config=self._tessConfig)
        guess_list = text.strip().lower().split('\n')

        # Validate guesses
        if any(g not in self._valid_words for g in guess_list):
            raise InvalidGame(f'Tesseract misidentified a word.\n  output = {guess_list}')

        # Return guesses as 2-D numpy array
        return np.array( [list(g) for g in guess_list] )

    def getResponse(self, solved: bool, numGuesses: int) -> str:
        if not solved:
            numGuesses = 0

        return choice(self._responses[numGuesses])

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
        """

        # Read user guesses
        guesses = self._guessesFromImage(image)

        # get word of the day as well as the wordle number
        wotd, wrdl_num = get_wotd(submissionDate, wrdl_num=True)
        orig_counts = Counter(wotd)

        # Initialize scores
        scores = np.full(shape=guesses.shape, fill_value=Score.INCORRECT)
        uniques = [set() for _ in range(5)]
        tC = tM = uC = uM = 0

        # Score the game
        # It's easier to score yellows after greens as opposed to "inline". Otherwise,
        #   we would have to look ahead for potential greens because green has a higher
        #   precedence and therefore consumes one of the characters counts before any
        #   would-be yellows have the chance.
        for row, guess in enumerate(guesses):
            counts = orig_counts.copy()
            remaining = []

            # score CORRECT LETTERS in CORRECT POSITION (Green)
            for col, (gc, wc) in enumerate(zip(guess, wotd)):
                if gc == wc:
                    scores[row,col] = Score.CORRECT
                    counts[gc] -= 1
                    tC += 1

                    #(1/2) start adding unique chars...
                    if gc not in uniques[col]:
                        uC += 1
                        uniques[col].add(gc)
                else:
                    remaining.append( (row, col, gc) )

            # score CORRECT LETTERS in WRONG POSITION (Yellow)
            for row, col, gc in remaining:
                if gc in wotd and counts[gc] > 0:
                    scores[row,col] = Score.MISPLACED
                    counts[gc] -= 1
                    tM += 1

                    if gc not in uniques[col]:
                        uM += 1

                #(2/2) ...finish adding unique chars
                uniques[col].add(gc)

        return GameStats(
            guessTable= guesses,
            numGuesses= guesses.shape[0],
            solution= wotd,
            uniqueCorrect= uC,
            uniqueMisplaced= uM,
            totalCorrect= tC,
            totalMisplaced= tM,
            won= all(s == Score.CORRECT for s in scores[-1]),
            uniqueAll= sum(len(set) for set in uniques)
        )


    ### Overridden Discord Bot class methods
    async def on_ready(self):

        # Wait for client cache to load
        await self.wait_until_ready()

        # Sync application commands
        if not self.synced:
            await self.tree.sync(guild=self.guild)
            self.synced = True

        # update log with startup time
        self.update_log(datetime.now(), 'Startup')

        print(f'{self.user} ready!')

    # updates the log with the provided information
    def update_log(self, dtime:datetime, event:str, exc_name:str='', server:str='', user:str='', win:str='', guesses:str='', greens:str='', yellows:str='', uniques:str='', traceback:TracebackType=None) -> None:
        # update the log with passed data
        self.log.update(dtime=dtime, event=event, exc_name=exc_name, server=server, user=user, win=win, guesses=guesses, greens=greens, yellows=yellows, uniques=uniques, traceback=traceback)


    # updates the database with the provided game
    def submit_game(self, date:datetime, user:str, game:GameStats) -> GameStats|None:
        '''
        Takes in a date, user and game (Gamestats object) and
        stores data in the database.

        ---
        Function handles DoubleSubmit exception and stores all submission events in log
        '''
        # try to add game to the database
        try:
            # submit game to the database
            baseStats, event_type = self.db.submit_data(
            username= user,
            dtime= date,
            win= game.won,
            guesses= game.numGuesses,
            greens= game.uniqueCorrect,
            yellows= game.uniqueMisplaced,
            uniques= game.uniqueAll)
            
            # log the submitted game
            self.update_log(date, event_type, user=user, win=game.won, guesses=game.numGuesses, greens=game.uniqueCorrect, yellows=game.uniqueMisplaced, uniques=game.uniqueAll)

            # return the baseStats for the submitted game
            return baseStats

        except DoubleSubmit:
            # update the log with the double submission
            self.update_log(date, 'DoubleSubmit', user=user)

            # return None as there is no game submitted
            return None
