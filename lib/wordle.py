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

MSG_DEL = '*<deleted {0}\'s message>*\n{1}'

# decorator function for timing purposes
def timer(func):
    def _inner(*args, **kwargs):
        beg = perf_counter()
        ret = func(*args, **kwargs)
        end = perf_counter()
        print(ansi.magenta(f'[{end-beg:.06f}]: {func.__name__}'))
        return ret
    return _inner

class WebScraper:
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

    def wotd(self) -> str:
        """Returns today's word."""

        now = datetime.now().date()
        if self._last_updated < now:
            self._last_updated = now
            self._wotd = self._scrape()

        return self._wotd

class ImageProcessor:
    """Reads an image of a users Wordle game to obtain their guesses.
        
    ---
    ## Methods
    
    getGuesses() -> list[str]
        Returns a list of the user's guesses."""

    def __init__(self, image: bytes) -> None:
        self._image = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        self._grayscale = cv2.cvtColor(self._image, cv2.COLOR_BGR2GRAY)
        self._darkTheme = np.median(self._grayscale[:1,:]) < 200
        self._cell_mask = self._genCellMask()
        self._cell_contours = self._genCellContours()
        self._chars_mask = self._genCharMask()

        self.guesses: list[str] = self._getGuesses()

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

    def _getGuesses(self) -> 'list[str]':
        """Use Tesseract to convert a mask of the user's guesses into a list of strings."""

        text:str = image_to_string(self._chars_mask, lang="eng", config='--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        return text.lower().strip().split('\n')

class CharScore(Enum):
    CORRECT = auto()
    MISPLACED = auto()
    INCORRECT = auto()

    def __str__(self):
        return self.name

class GameScorer:
    def __init__(self, image: bytes) -> None:
        self.ip = ImageProcessor(image)
        self.scraper = WebScraper()

        self.numGuesses = len(self.ip.guesses)
        self.scores = self._scoreGame()
        self.won = all(s == CharScore.CORRECT for s in self.scores[-1])

    # Returns the character, colored based on it's score.
    def _colorByScore(self, char, score) -> ansi.sgr:
        if score == CharScore.CORRECT:
            return ansi.green(char)

        if score == CharScore.MISPLACED:
            return ansi.yellow(char)

        if score == CharScore.INCORRECT:
            return ansi.rgb(char, r=150, g=150, b=150)

        # Invalid Character Score!
        print(f'Invalid score type <{score}>. Returning original character.')
        return char

    # Assigns each character a CharScore.
    def _scoreGame(self) -> 'list[list[CharScore]]':
        # Score each guess
        wotd = self.scraper.wotd()
        wotd_char_counts = Counter(wotd)
        results = []
        for guess in self.ip.guesses:
            scores = [CharScore.INCORRECT] * 5
            remaining = []

            # Mark all correct characters
            for i, (gchar, wchar) in enumerate(zip(guess, wotd)):
                if gchar == wchar:
                    wotd_char_counts[wchar] -= 1
                    scores[i] = CharScore.CORRECT
                else:
                    remaining.append(i)

            # Mark all misplaced characters
            for index in remaining:
                gchar = guess[index]
                wchar = wotd[index]
                if gchar in wotd:
                    if wotd_char_counts[gchar] > 0:
                        wotd_char_counts[gchar] -= 1
                        scores[index] = CharScore.MISPLACED
            
            results.append(scores)
        return results

    # Returns a list of colored guesses according to the Wordle scheme.
    def _pretty(self) -> 'list[str]':
        # For each guess...
        pretty = []
        for guess, scores in zip(self.ip.guesses, self.scores):
            # For each character in the guess...
            str_score = ''
            for char, score in zip(guess, scores):
                str_score += str(self._colorByScore(char, score))
            pretty.append(str_score)
        return pretty

class Bot:
    def __init__(self, token: str, id: int) -> None:
        self.token = token
        self.guild = discord.Object(id=id)
        self.synced = False
        self.bot = commands.Bot(
            command_prefix='!',
            intents=discord.Intents.all(),
            help_command=None)
        
        ### Discord Bot Events
        @self.bot.event
        async def on_ready():
            await self.bot.wait_until_ready()
            if not self.synced:
                await self.bot.tree.sync(guild=self.guild)
                self.synced = True

            print(f'\'{self.bot.user}\' logged in and ready!')

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return

            if message.attachments:
                # Restrict attachments to one per message
                if len(message.attachments) > 1:
                    await message.delete()
                    await message.channel.send(MSG_DEL.format(message.author.name, 'One at a time please!'))
                    return

                # Only allow if it's tagged with spoiler
                user_attachment = message.attachments[0]
                if not user_attachment.is_spoiler():
                    await message.delete()
                    await message.channel.send(MSG_DEL.format(message.author.name, 'Please mark your image as spoiler 😎'))
                    return

                # Capture the game
                img = await user_attachment.read()
                game = GameScorer(image=img)
                resp = self._getResponse(game)
                await message.channel.send(resp)
                return

            # Remind the discord.ext.commands.Bot to parse the message for commands
            await self.bot.process_commands(message)

        ### Discord Bot Application Commands
        @self.bot.tree.command(name='chimp', description='Are you smarter than a chimp? Play this quick memorization game to find out!', guild=self.guild)
        async def _(interaction: discord.Interaction):
            chimp = ChimpView()
            await interaction.response.send_message(view=chimp)

        @self.bot.tree.command(name='link', description='Get the link to the Wordle webpage.', guild=self.guild)
        async def _(interaction: discord.Interaction):
            await interaction.response.send_message(view=self._genLinkView(), ephemeral=True)

        @self.bot.tree.command(name='roll', description='Roll an N-sided die!', guild=self.guild)
        async def _(interaction: discord.Interaction, faces: discord.app_commands.Range[int, 2, None]):
            await interaction.response.send_message(f'You rolled a {randint(1, faces)}!')

        @self.bot.tree.command(name='choose', description='Randomly choose ONE item from a list of words separated by spaces.', guild=self.guild)
        async def _(interaction: discord.Interaction, choices: str):
            await interaction.response.send_message(choice(choices.split()))

    def _genLinkView(self) -> discord.ui.View:
        return discord.ui.View(timeout=0).add_item(
            discord.ui.Button(
                label='Play Wordle',
                style=discord.ButtonStyle.link,
                url='https://www.nytimes.com/games/wordle/index.html'))

    def _getResponse(self, game: GameScorer) -> str:
        if game.won:
            if game.numGuesses < 3:
                return choice(['damn that\'s crazy.. i have google too 🙄', 'suuuuuuuure\nyou just *knew* it right? 🤔'])
            
            if game.numGuesses < 5:
                return choice(['ok', 'yea', 'yep', 'that\'s definitely a game'])

            return choice([f'it actually took you {game.numGuesses} guess{"es" if game.numGuesses > 1 else ""}. lmao.', 'garbage'])
        return choice(['you suck!', 'better luck next time idiot'])

    def run(self) -> None:
        self.bot.run(token=self.token)
        print('Bot exited.')
