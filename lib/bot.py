# DiscordPy Manual: https://discordpy.readthedocs.io/en/stable/api.html

from discord.ext import commands
from discord import File, Embed, Message
from wordle_image_processing import get_guesses
import wordle_scoring as ws
from credentials import bot_token

# CONSTANTS ################################################################################
############################################################################################
BOT = commands.Bot(command_prefix='!')
LINK_FILENAME = 'wordle.jpg'

# COMMANDS #################################################################################
############################################################################################
# link: ____________________________________________________________________________________
# Replies with an embeded message containing a link to the Wordle website.
@BOT.command(name='link')
async def link(context):
    await context.send(
        embed=Embed(
            color       = 0x121212,
            title       = 'Wordle - A daily word game',
            url         = 'https://www.nytimes.com/games/wordle/index.html',
            description = 'Guess the hidden word in 6 tries. A new puzzle is available each day.').set_image(
                url     = 'attachment://' + LINK_FILENAME),
        file=File('./lib/images/' + LINK_FILENAME))
    return

# kill: ____________________________________________________________________________________
# Kills the bot.
@BOT.command(name='kill')
async def kill(context):
    filename = './lib/images/yes_honey.png'
    with open(filename, 'rb') as f:
        discordFile = File(f, filename=filename)

    await context.send(file=discordFile)
    quit('Bot killed.')

# EVENTS ###################################################################################
############################################################################################

# on_ready: ________________________________________________________________________________
# Print message when the bot is connected.
@BOT.event
async def on_ready():
    print(f'Discord user \"{BOT.user}\" connected.')

# on_message: ______________________________________________________________________________
# Reply to images. Currently assumes all images are Wordle postgame screenshots.
@BOT.event
async def on_message(message:Message):
    # Don't reply to self
    if message.author == BOT.user:
        return

    # If message contains attachments...
    elif message.attachments:
        for att in message.attachments:
            img_bytes = await att.read()
            guesses = get_guesses(img_bytes)
            game = ws.PlayerGame(guesses)

            if game.won:
                response = f'Wow, it really took you {game.guessCount} guess{"es" if game.guessCount > 1 else ""}? Lmao.'
            else:
                response = 'you suck!'

            await message.channel.send(response)

    await BOT.process_commands(message)

# !!! BLOCKING !!! BLOCKING !!! BLOCKING !!! BLOCKING !!! BLOCKING !!! BLOCKING !!! BLOCKING
# Start the Discord bot.
BOT.run(bot_token)
print('bot.py DONE')