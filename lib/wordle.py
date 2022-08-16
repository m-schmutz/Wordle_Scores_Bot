from typing import Any, Literal, Optional, Union
import numpy as np
import cv2
import discord

from discord.ext import commands
from pytesseract import image_to_string
from selenium import webdriver
from selenium.webdriver.firefox.service import Service

from time import perf_counter
from datetime import datetime
from enum import Enum, auto
from collections import Counter
from random import choice, randint

import ansi
from chimp import ChimpView
from database import BaseStats, BotDatabase, DoubleSubmit

from inspect import cleandoc

def timer(func):
    def _inner(*args, **kwargs):
        beg = perf_counter()
        ret = func(*args, **kwargs)
        end = perf_counter()
        print(ansi.magenta(f'[{end-beg:.06f}]: {func.__name__}'))
        return ret
    return _inner



class UnidentifiableGame(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.message = '***I DO NOT UNDERSTAND, TRY A DIFFERENT IMAGE***'

class CharScore(Enum):
    CORRECT = auto()
    MISPLACED = auto()
    INCORRECT = auto()

    def __repr__(self) -> str:
        return self.name

class SubmissionReply(discord.Embed):
    def __init__(self, *, username: str, stats: BaseStats, description: Optional[str] = None, timestamp: Optional[datetime] = None):
        super().__init__(
            color= discord.Color.random(),
            title= f'>>> Results for {username}',
            description= description,
            timestamp= timestamp)

        # self.set_image(url='https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fimgc.allpostersimages.com%2Fimg%2Fposters%2Fsteve-buscemi-smiling-in-close-up-portrait_u-L-Q1171600.jpg%3Fh%3D550%26p%3D0%26w%3D550%26background%3Dffffff&f=1&nofb=1')
        self.add_field(name='Guess Distribution', value=stats.guessDistribution, inline=False)
        self.add_field(name='Games Played', value=stats.numGamesPlayed, inline=False)
        self.add_field(name='Win Rate', value=f'{stats.winRate:.02f}%', inline=False)
        self.add_field(name='Streak', value=stats.streak, inline=False)
        self.add_field(name='Max Streak', value=stats.maxStreak, inline=False)

class _wotdScraper:
    """Keeps track of the Word of the Day. Uses Selenium to scrape the NYTimes Wordle webpage."""

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

    def wotd(self, date: datetime) -> str:
        """Returns today's word."""

        # Potentially update today's word
        today = datetime.now().date()
        if self._last_updated < today:
            prev_wotd = self._wotd
            self._wotd = self._scrape()
            self._last_updated = today

            # If we updated the word as user submit, return the previous word
            if date < today:
                return prev_wotd

        return self._wotd

class _imageProcessor:
    """Reads an image of a users Wordle game to obtain their guesses."""

    def __init__(self) -> None:
        self._MAX_DARK = int(200)
        self._MAX_THRESH = int(255)

    def _genCellContours(self, grayscale: cv2.Mat, darkTheme: bool) -> 'list[np.ndarray]':
        # Create and use the cell mask to find the cell contours.
        if darkTheme:
            _, cell_mask = cv2.threshold(grayscale, 30, self._MAX_THRESH, cv2.THRESH_BINARY)
        else:
            _, cell_mask = cv2.threshold(grayscale, self._MAX_DARK, self._MAX_THRESH, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(cell_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Remove non-quadrilaterals and non-squares
        filtered = []
        for c in contours:
            if c.size != 8:
                continue
            
            _,_,w,h = cv2.boundingRect(c)
            if abs(w-h) > (w+h)*0.015:
                continue

            filtered.append(c)
        assert all(elem.shape == (4,1,2) for elem in filtered), ansi.red('Not all contours have the shape (4,1,2).')

        # Remove all axis of length one since they are useless. Additionally, reverse
        # the list since findContours works from SE to NW and we want our contours
        # organized from NW to SE (i.e. guess order).
        return np.squeeze(filtered)[::-1]

    def _genMask(self, image: cv2.Mat) -> cv2.Mat:
        grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        darkTheme = (np.median(grayscale[:1,:]) < self._MAX_DARK)

        _, mask = cv2.threshold(grayscale, self._MAX_DARK, self._MAX_THRESH, cv2.THRESH_BINARY_INV)
        cell_contours = self._genCellContours(grayscale, darkTheme)
        if len(cell_contours) != 30:
            raise UnidentifiableGame

        # squeeze letters horizontally
        cols = []
        for c in cell_contours[:5]:
            x,_,w,_ = cv2.boundingRect(c)
            off = w // 4
            cols.append(mask[:, x+off : x+w-off])
        mask: cv2.Mat = cv2.hconcat(cols)

        # crop vertically
        ys = set(
            y
            for contour in cell_contours
            for (_, y) in contour)
        mask: np.ndarray = mask[min(ys):max(ys), :]

        # potentially fill empty horizontal strips
        if not darkTheme:
            for i in range(mask.shape[0]):
                if all(mask[i,:] == 0):
                    mask[i,:] = self._MAX_THRESH

        return mask

    def getGuesses(self, image: bytes) -> 'list[str]':
        """Use Tesseract to convert a mask of the user's guesses into a list of strings."""

        # Convert Discord image (bytes) to OpenCV image (Mat)
        mat = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)

        # Generate mask and feed Tesseract :) *pat* *pat* good boy
        text = image_to_string(
            image= self._genMask(mat),
            lang= "eng",
            config= '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        # Convert raw string into list
        return text.lower().strip().split('\n')

class _gameAnalyzer:
    def __init__(self) -> None:
        self._imgproc = _imageProcessor()
        self._scraper = _wotdScraper()
        self._initGameData()

    def _initGameData(self, guesses: list = [], wotd: str = ''):
        self.guesses = guesses
        self.numGuesses = len(guesses)
        self.scores = []
        self.numGreen = 0
        self.numYellow = 0
        self.wotd = wotd
        self.defaultCounts = Counter(wotd)
        self.defaultScore = [CharScore.INCORRECT] * 5

    # Assigns each character a CharScore.
    def scoreGame(self, image: bytes, submissionDate: datetime) -> 'tuple[bool, int, int, int]':
        """Parse a screenshot of a Wordle game and return information about the game.
        
        ---
        ## Parameters

        image : `bytes`
            The user-provided screenshot of their Wordle game.

        submissionDate : `datetime`
            A datetime object respresenting the time of submission.

        ---
        ## Returns

            self.solved : `bool` ,

            self.numGuesses : `int` ,

            self.numGreen : `int` ,

            self.numYellow : `int`

        ---
        ## Raises

        UnidentifiableGame
            Unable to find a game in the image.
        """

        # Get user guesses and initialize game data
        self._initGameData(
            guesses= self._imgproc.getGuesses(image),
            wotd= self._scraper.wotd(submissionDate))

        # Score each guess
        for guess in self.guesses:
            score = self.defaultScore.copy()
            counts = self.defaultCounts.copy()
            remaining: list[tuple] = []

            # Mark all correct characters
            for i, gchar, wchar in zip(range(5), guess, self.wotd):
                if gchar == wchar:
                    score[i] = CharScore.CORRECT
                    counts[wchar] -= 1
                    self.numGreen += 1
                else:
                    remaining.append((i, gchar))

            # Mark all misplaced characters
            for i, gchar in remaining:
                if gchar in self.wotd and counts[gchar] > 0:
                    score[i] = CharScore.MISPLACED
                    counts[gchar] -= 1
                    self.numYellow += 1

            self.scores.append(score)
        self.solved = all(s == CharScore.CORRECT for s in self.scores[-1])

        # -> (SOLVED bool, #GUESSES int, #GREEN int, #YELLOW int)
        return (self.solved, self.numGuesses, self.numGreen, self.numYellow)



class Bot:
    def __init__(self, token: str, id: int) -> None:
        self._token = token
        self._guild = discord.Object(id=id)
        self._synced = False
        self._ga = _gameAnalyzer()
        self._db = BotDatabase(db_path='./lib/stats.db')
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
            # Shhhhhhhhhhhh we'll get there, Discord...
            await interaction.response.defer()
            date = interaction.created_at.astimezone().date()

            # Find the game and score it
            try:
                results = self._ga.scoreGame(await image.read(), date)
            except UnidentifiableGame as e:
                await interaction.followup.send(content=e.message, ephemeral=True)
                return

            # Submit to database
            try:
                stats = self._db.submit_data(str(interaction.user), date, *results)
            except DoubleSubmit as e:
                await interaction.followup.send(content=e.message, ephemeral=True)
                return

            # Reply with stats
            await interaction.followup.send(
                embed= SubmissionReply(
                    username= interaction.user.name,
                    stats= stats),
                file= await image.to_file(spoiler=True))

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

    def _getResponse(self, solved: bool, numGuesses: int, *argeater) -> str:
        if solved:
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
