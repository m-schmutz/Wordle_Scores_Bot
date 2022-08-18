from typing import Optional
import numpy as np
import cv2
import discord
from discord import Intents, Object
from discord.ext import commands
from pytesseract import image_to_string
from selenium import webdriver
from selenium.webdriver.firefox.service import Service

from time import perf_counter
from datetime import datetime
from enum import Enum, auto
from collections import Counter
from random import choice
from dataclasses import dataclass

import ansi
from database import BaseStats, BotDatabase

def timer(func):
    def _inner(*args, **kwargs):
        beg = perf_counter()
        ret = func(*args, **kwargs)
        end = perf_counter()
        print(ansi.magenta(f'[{end-beg:.06f}]: {func.__name__}'))
        return ret
    return _inner


@dataclass
class WordleGame:
    guessTable: np.ndarray
    numGuesses: int
    solution: str
    won: bool
    uniqueCorrect: int
    uniqueMisplaced: int
    uniqueAll: int
    totalCorrect: int
    totalMisplaced: int

class UnidentifiableGame(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.message = '***I DO NOT UNDERSTAND, TRY A DIFFERENT IMAGE***'

class CharScore(Enum):
    CORRECT = auto()
    MISPLACED = auto()
    INCORRECT = auto()

    def __repr__(self) -> str:
        char = self.name[0]

        if self == self.CORRECT:
            return ansi.green(char)
        if self == self.MISPLACED:
            return ansi.yellow(char)
        return ansi.bright_black(char)

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

class WebScraper:
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

class WordleBot(commands.Bot):
    def __init__(self, server_id: int) -> None:
        super().__init__(
            command_prefix= '!',
            intents= Intents.all(),
            help_command= None)
        self.synced = False
        self.guild = Object(id=server_id)
        self.scraper = WebScraper()
        self.db = BotDatabase(db_path='./lib/stats.db')

    ### Overridden methods
    async def on_ready(self):

        # Wait for client cache to load
        await self.wait_until_ready()

        # Sync application commands
        if not self.synced:
            await self.tree.sync(guild=self.guild)
            self.synced = True

        print(f'{self.user} ready!')

    ### Additional methods
    def _getResponse(self, solved: bool, numGuesses: int, *argeater) -> str:
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

    def _guessesFromImage(self, image: bytes) -> np.ndarray:
        """Use Tesseract to convert a mask of the user's guesses into a list of strings.
        
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

        UnidentifiableGame
            Unable to find a game in the image."""

        # Convert Discord image (bytes) to OpenCV image (Mat)
        imageMat = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)

        grayscale = cv2.cvtColor(imageMat, cv2.COLOR_BGR2GRAY)
        darkTheme = (np.median(grayscale[:1,:]) < 200)

        # Create and use the cell mask to find the cell contours.
        contours, _ = cv2.findContours(
            image= cv2.threshold(grayscale, 30, 255, cv2.THRESH_BINARY)[1]
                if darkTheme
                else cv2.threshold(grayscale, 200, 255, cv2.THRESH_BINARY_INV)[1],
            mode= cv2.RETR_EXTERNAL,
            method= cv2.CHAIN_APPROX_SIMPLE)

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
        cell_contours = np.squeeze(filtered)[::-1]

        if len(cell_contours) % 5:
            raise UnidentifiableGame

        _, mask = cv2.threshold(grayscale, 200, 255, cv2.THRESH_BINARY_INV)

        # squeeze letters horizontally
        cols = []
        for c in cell_contours[:5]:
            x,y,w,_ = cv2.boundingRect(c)
            off = w // 4
            cols.append(mask[:, x+off : x+w-off])
        mask: cv2.Mat = cv2.hconcat(cols)

        # crop vertically
        ys = set(
            y
            for contour in cell_contours
            for (_, y) in contour)
        mask: np.ndarray = mask[min(ys):max(ys), :]
        print(len(ys), ys)

        # potentially fill empty horizontal strips
        if not darkTheme:
            for i in range(mask.shape[0]):
                if all(mask[i,:] == 0):
                    mask[i,:] = 255

        # Generate mask and feed Tesseract :) *pat* *pat* good boy
        text = image_to_string(
            image= mask,
            lang= "eng",
            config= '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        # Convert raw string into list
        lst = text.lower().strip().split('\n')
        arr = np.zeros(shape=(len(lst),5), dtype=str)
        for row, guess in enumerate(lst):
            for i, c in enumerate(guess):
                arr[row,i] = c
        return arr

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
            remaining: list[tuple] = []
            counts: Counter = counts.copy()

            # score CORRECT LETTERS in CORRECT POSITION (Green)
            for col, gc, wc in zip(range(5), guess, wotd):
                if gc == wc:
                    scores[row,col] = CharScore.CORRECT
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
                    scores[row,col] = CharScore.MISPLACED
                    counts[gc] -= 1
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
