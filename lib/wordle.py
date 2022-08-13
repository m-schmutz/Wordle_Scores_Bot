import numpy as np
import cv2
import discord
import ansi
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from pytesseract import image_to_string
from datetime import datetime
from time import perf_counter
from discord.ext import commands
from random import choice, randint
from chimp import ChimpView
from enum import Enum, auto
from collections import Counter
from database import BotDatabase, DoubleSubmit

# decorator function for timing purposes
def timer(func):
    def _inner(*args, **kwargs):
        beg = perf_counter()
        ret = func(*args, **kwargs)
        end = perf_counter()
        print(ansi.magenta(f'[{end-beg:.06f}]: {func.__name__}'))
        return ret
    return _inner

PREV_PATH = './lib/prev.wotd'
class _WebScraper:
    """Keeps track of the Word of the Day. Uses Selenium to scrape the NYTimes Wordle webpage.
    
    ---
    ## Methods
    
    wotd() -> str
        Returns the Word of the Day."""

    def __init__(self) -> None:
        options = webdriver.FirefoxOptions()
        options.headless = True
        options.page_load_strategy = 'eager'
        service = Service(log_path='./lib/geckodriver.log')

        self._driver = webdriver.Firefox(options=options, service=service)
        self._last_updated = datetime.now().date()
        self._wotd = self._scrape()

    def __del__(self) -> None:
        # WILL CAUSE MEMORY LEAK IF NOT CLOSED
        self._driver.quit()

    def _scrape(self) -> str:
        """Webscrapes the official webpage to obtain the Word of the Day."""

        self._driver.get('https://www.nytimes.com/games/wordle/index.html')
        return str(self._driver.execute_script('return JSON.parse(this.localStorage.getItem("nyt-wordle-state")).solution'))

    def wotd(self, subDate: datetime) -> str:
        """Returns today's word."""

        # Potentially update today's word
        today = datetime.now().date()
        if self._last_updated < today:
            prev_wotd = self._wotd
            self._wotd = self._scrape()
            self._last_updated = today

            # If we updated the word as user submit, return the previous word
            if subDate < today:
                return prev_wotd

        return self._wotd

class _ImageProcessor:
    """Reads an image of a users Wordle game to obtain their guesses.
        
    ---
    ## Methods
    
    getGuesses(image: bytes) -> list[str]
        Returns a list of the user's guesses."""

    def __init__(self) -> None:
        self._grayscale = None
        self._darkTheme = None
        self._cell_mask = None
        self._cell_contours = None
        self._chars_mask = None

    def _genCellMask(self) -> cv2.Mat:
        if self._darkTheme:
            thresh = 30
            mode = cv2.THRESH_BINARY
        else:
            thresh = 200
            mode = cv2.THRESH_BINARY_INV

        _, mask = cv2.threshold(self._grayscale, thresh, 255, mode)
        return mask

    def _genCellContours(self) -> 'list[np.ndarray]':
        contours, _ = cv2.findContours(self._cell_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Remove non-quadrilaterals and non-squares
        filtered = list()
        for c in contours:
            if c.size != 8:
                continue
            
            _,_,w,h = cv2.boundingRect(c)
            if abs(w-h) > (w+h)*0.015:
                continue

            filtered.append(c)

        # Remove all axis of length one since they are useless. Additionally, reverse
        # the list since findContours works from SE to NW and we want our contours
        # organized from NW to SE (i.e. guess order).
        assert all(elem.shape == (4,1,2) for elem in filtered), ansi.red('Not all contours have the shape (4,1,2).')
        return np.squeeze(filtered)[::-1]

    def _genCharMask(self) -> cv2.Mat:
        _, mask = cv2.threshold(self._grayscale, 200, 255, cv2.THRESH_BINARY_INV)

        # squeeze letters horizontally
        cols = list()
        for c in self._cell_contours[:5]:
            x,_,w,_ = cv2.boundingRect(c)
            off = w // 4
            cols.append(mask[:, x+off : x+w-off])
        mask = cv2.hconcat(cols)

        # crop vertically
        ys = list(
            y
            for contour in self._cell_contours
            for (_, y) in contour)
        mask = mask[min(ys):max(ys), :]

        # potentially fill empty horizontal strips
        if not self._darkTheme:
            for i in range(mask.shape[0]):
                if all(mask[i,:] == 0):
                    mask[i,:] = 255

        return mask

    def _tesseract(self) -> 'list[str]':
        """Use Tesseract to convert a mask of the user's guesses into a list of strings."""

        text:str = image_to_string(self._chars_mask, lang="eng", config='--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        return text.lower().strip().split('\n')

    def getGuesses(self, image: bytes) -> 'list[str]':
        self._grayscale = cv2.cvtColor(
            src = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR),
            code = cv2.COLOR_BGR2GRAY)
        self._darkTheme = (np.median(self._grayscale[:1,:]) < 200)
        self._cell_mask = self._genCellMask()
        self._cell_contours = self._genCellContours()
        self._chars_mask = self._genCharMask()

        guesses = self._tesseract()
        self.__init__()
        return guesses

class _CharScore(Enum):
    CORRECT = auto()
    MISPLACED = auto()
    INCORRECT = auto()

    def __repr__(self) -> str:
        return self.name

class _GameAnalyzer:
    # Assigns each character a _CharScore.
    def scoreGame(self, guesses: 'list[str]', wotd: str) -> 'tuple[bool, int, int, int]':
        self.numGuesses = len(guesses)
        self.numGreen = 0
        self.numYellow = 0

        wotd_char_counts = Counter(wotd)
        results = []

        # Score each guess
        for guess in guesses:
            scores = [_CharScore.INCORRECT] * 5
            remaining = list()

            # Mark all correct characters
            for i, gchar, wchar in zip(range(5), guess, wotd):
                if gchar == wchar:
                    wotd_char_counts[wchar] -= 1
                    scores[i] = _CharScore.CORRECT
                    self.numGreen += 1
                else:
                    remaining.append(i)

            # Mark all misplaced characters
            for index in remaining:
                gchar = guess[index]
                wchar = wotd[index]
                if gchar in wotd and wotd_char_counts[gchar] > 0:
                    wotd_char_counts[gchar] -= 1
                    scores[index] = _CharScore.MISPLACED
                    self.numYellow += 1

            results.append(scores)

        self.won = all(s == _CharScore.CORRECT
            for s in results[-1])

        return (self.won, self.numGuesses, self.numGreen, self.numYellow)

    # Returns a list of colored guesses according to the Wordle scheme.
    def _pretty(self) -> 'list[str]':
        # For each guess...
        pretty = []
        for guess, scores in zip(self._ip.guesses, self.scores):
            # For each character in the guess...
            str_score = ''
            for char, score in zip(guess, scores):
                if score == _CharScore.CORRECT:
                    str_score += ansi.green(char)
                elif score == _CharScore.MISPLACED:
                    str_score += ansi.yellow(char)
                elif score == _CharScore.INCORRECT:
                    str_score += ansi.rgb(char, r=150, g=150, b=150)
                else:
                    print(f'Invalid score type <{score}>. Returning original character.')
            pretty.append(str_score)
        return pretty

class Bot:
    def __init__(self, token: str, id: int) -> None:
        self._token = token
        self._guild = discord.Object(id=id)
        self._synced = False
        self._scraper = _WebScraper()
        self._ip = _ImageProcessor()
        self._ga = _GameAnalyzer()
        self._db = BotDatabase(db_path='./lib/stats._db')
        self._bot = commands.Bot(
            command_prefix = '!',
            intents = discord.Intents.all(),
            help_command = None)

        ### Discord Bot Events
        @self._bot.event
        async def on_ready():
            await self._bot.wait_until_ready()
            if not self._synced:
                await self._bot.tree.sync(guild=self._guild)
                self._synced = True

            print(f'\'{self._bot.user}\' logged in and ready!')

        ### Discord Bot Application Commands
        @self._bot.tree.command(name= 'submit',
            description= 'Submit a screenshot of your Wordle game!',
            guild= self._guild)
        async def _(interaction: discord.Interaction, image: discord.Attachment):

            # Defer the response. Processing the game may take longer than 3 seconds.
            await interaction.response.defer(ephemeral=True, thinking=True)

            # Get data
            subDate = interaction.created_at.astimezone().date() # submission date
            wotd = self._scraper.wotd(subDate)
            guesses = self._ip.getGuesses(await image.read())
            results = self._ga.scoreGame(guesses, wotd)

            # Send to database and reply
            try:
                self._db.submit_data(str(interaction.user), *results, subDate)
            except DoubleSubmit:
                await interaction.followup.send(
                    content= 'You already submit today\'s game :)',
                    ephemeral= True)
            else:
                await interaction.followup.send(
                    file= await image.to_file(spoiler=True),
                    content= f'{interaction.user.mention}\'s submission:')
                await interaction.followup.send(
                    content= self._getResponse(*results),
                    ephemeral= True)

        @self._bot.tree.command(name= 'chimp',
            description= 'Are you smarter than a chimp? Play this quick memorization game to find out!',
            guild= self._guild)
        async def _(interaction: discord.Interaction):
            chimp = ChimpView()
            await interaction.response.send_message(view=chimp)

        @self._bot.tree.command(name= 'link',
            description= 'Get the link to the Wordle webpage.',
            guild= self._guild)
        async def _(interaction: discord.Interaction):
            await interaction.response.send_message(
                view= discord.ui.View(timeout=0).add_item(
                    discord.ui.Button(
                        label= 'Play Wordle',
                        style= discord.ButtonStyle.link,
                        url= 'https://www.nytimes.com/games/wordle/index.html')),
                ephemeral= True)

        @self._bot.tree.command(name='roll',
            description= 'Roll an N-sided die!',
            guild= self._guild)
        async def _(interaction: discord.Interaction, faces: discord.app_commands.Range[int, 2, None]):
            await interaction.response.send_message(f'You rolled a {randint(1, faces)}!')

    def _getResponse(self, won: bool, numGuesses: int, *argeater) -> str:
        if won:
            if numGuesses < 3:
                return choice(['damn that\'s crazy.. i have google too 🙄', 'suuuuuuuure\nyou just *knew* it right? 🤔'])
            
            if numGuesses < 5:
                return choice(['ok?', 'yea', 'cool', 'yep', 'that\'s definitely a game'])

            return choice([f'it actually took you {numGuesses} guess{"es" if numGuesses > 1 else ""}. lmao.', 'garbage'])
        return choice(['you suck!', 'better luck next time idiot'])

    def run(self) -> None:
        """WARNING: This does not return until the bot stops."""

        self._bot.run(token=self._token)
        print('Bot exited.')
