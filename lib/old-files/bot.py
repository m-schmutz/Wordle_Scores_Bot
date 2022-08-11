import discord
from discord.ext import commands
import random
from credentials import bot_token, server_id
from chimp import ChimpView
from wordle_image_processing import guessesFromImage
from wordle_scoring import WordleGame


# Dummy database
class Database:
    def __init__(self) -> None:
        pass
    def update_user(self, username: str, solved: bool, guesses: int, greens: int, yellows: int):
        return

class WordleBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix = '!',
            intents = discord.Intents.all(),
            help_command=None)
        self.synced = False
        self.guild = discord.Object(id=server_id)

    # OVERRIDE discord.on_ready():
    # Waits for the bot's cache to load to sync the command tree.
    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await self.tree.sync(guild=self.guild)
            self.synced = True

        print(f'\'{self.user}\' logged in and ready!')

    async def _processAttachments(self, message: discord.Message):
        # Restrict attachments to one per message
        if len(message.attachments) > 1:
            await message.delete()
            await message.channel.send(
                f'*<deleted {message.author.name}\'s message>* One at a time please!\n\
                (っ◔◡◔)っ ♥ that\'s what she said ♥')
            return

        # Get the single attachment
        user_attachment = message.attachments[0]

        # Only allow if it's tagged with spoiler
        if not user_attachment.is_spoiler():
            await message.delete()
            await message.channel.send(
                f'*<deleted {message.author.name}\'s image>*\n\
                Please mark your image as spoiler 😎')
            return

        # Capture the game
        
        # await message.channel.send(
        #     content = self.responseToGame(
        #         game = WordleGame(
        #             guesses = guessesFromImage(
        #                 bytes = await user_attachment.read()))))
        return

    # OVERRIDE discord.on_message():
    # Upon receiving attachments, ensures they are marked as spoiler and
    # only uploaded one at a time before scoring and replying.
    # Lastly, allows self.process_commands() to parse the message.
    async def on_message(self, message: discord.Message):
        if message.author.bot: return

        # If message contains attachments...
        if message.attachments:
            await self._processAttachments(message)

        # Remind the discord.ext.commands.Bot to parse the message for commands
        await self.process_commands(message)
        return

    # Builds and returns a View with a single Button link.
    def genLinkView(self):
        return discord.ui.View(timeout=0).add_item(
            discord.ui.Button(
                label='Play Wordle',
                style=discord.ButtonStyle.link,
                url='https://www.nytimes.com/games/wordle/index.html'))

    # Returns a response depending on the outcome.
    def responseToGame(self, game: WordleGame) -> str:
        if game.won:
            if game.numGuesses < 3:
                return random.choice(['damn that\'s crazy.. i have google too 🙄', 'suuuuuuuure\nyou just *knew* it right? 🤔'])
            
            if game.numGuesses < 5:
                return random.choice(['ok', 'yea', 'yep', 'that\'s definitely a game'])

            return random.choice([f'it actually took you {game.numGuesses} guess{"es" if game.numGuesses > 1 else ""}. lmao.', 'garbage'])
        return random.choice(['you suck!', 'better luck next time idiot'])


bot = WordleBot()

### APPLICATION COMMANDS ######################################################################
### /chimp
# chimp game
@bot.tree.command(name='chimp', description='Are you smarter than a chimp? Play this quick memorization game to find out!', guild=bot.guild)
async def chimp(interaction: discord.Interaction):
    chimp = ChimpView()
    chimp.randomizeBoard()
    await interaction.response.send_message(view=chimp)
    return

### /link _________________________________________________________________________________
# Replies to the channel with a Button to Wordle webpage.
@bot.tree.command(name='link', description='Get the link to the Wordle webpage.', guild=bot.guild)
async def link(interaction: discord.Interaction):
    await interaction.response.send_message(view=bot.genLinkView(), ephemeral=True)
    return

### /roll faces:int _______________________________________________________________________
# Replies with a random number in the range [1, faces].
@bot.tree.command(name='roll', description='Roll an N-sided die!', guild=bot.guild)
async def roll(interaction: discord.Interaction, faces: discord.app_commands.Range[int, 2, None]):
    roll = random.randint(1, faces)
    await interaction.response.send_message(f'You rolled a {roll}!')
    return

### /choose choices:str ___________________________________________________________________
# Replies with a random element in the user-provided list of words split by spaces.
@bot.tree.command(name='choose', description='Randomly choose ONE item from a list of words separated by spaces.', guild=bot.guild)
async def choose(interaction: discord.Interaction, choices: str):
    choice = random.choice(choices.split())
    await interaction.response.send_message(choice)
    return


### START THE BOT #############################################################################
bot.run(bot_token)
print('bot.py DONE')