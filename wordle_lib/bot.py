#!./env/bin/python3

# DiscordPy Manual: https://discordpy.readthedocs.io/en/stable/api.html
from discord.ext import commands
from discord import File, Embed
from wordle_image_processing import get_guesses
from credentials import bot_token
import wordle_scoring as ws

# CONSTANTS ################################################################################
############################################################################################
CMD_LINK        = 'link'
EMBED_COLOR     = 0x121212
EMBED_DESC      = 'Guess the hidden word in 6 tries. A new puzzle is available each day.'
EMBED_FILENAME  = 'wordle.jpg'
EMBED_TITLE     = 'Wordle - A daily word game'
EMBED_URL       = 'https://www.nytimes.com/games/wordle/index.html'

bot = commands.Bot(command_prefix='!')



# COMMANDS #################################################################################
############################################################################################

# link: ____________________________________________________________________________________
# Replies with an embeded message containing a link to the Wordle website.
@bot.command(name=CMD_LINK)
async def link(context):
    file        = File('./' + EMBED_FILENAME)
    embed       = Embed(
        color       = EMBED_COLOR,
        title       = EMBED_TITLE,
        url         = EMBED_URL,
        description = EMBED_DESC )

    embed.set_image(url='attachment://' + EMBED_FILENAME)

    await context.send(file=file, embed=embed)
    return

# kill: ____________________________________________________________________________________
# Kills the bot.
@bot.command(name="kill")
async def kill(context):
    # fn = "./debug_images_dump/yes_honey.png"
    # with open(fn, "rb") as fh:
    #     f = discord.File(fh, filename=fn)

    # await context.send(file=f)
    quit("Bot killed.")



# EVENTS ###################################################################################
############################################################################################

# on_ready: ________________________________________________________________________________
# Print message when the bot is connected.
@bot.event
async def on_ready():
    print(f'Discord user \"{bot.user}\" connected.')

# on_message: ______________________________________________________________________________
# Reply to images. Currently assumes all images are Wordle postgame screenshots.
@bot.event
async def on_message(message):
    # Don't reply to self
    if message.author == bot.user:
        return

    # If message contains attachments...
    elif message.attachments:
        # print(type(message.attachments))
        for att in message.attachments:
            img = await att.read()
            guesses = get_guesses(img)
            num_guesses = len(guesses)
            # scores = ws.score_game(guesses, guesses[-1])
            # plain = ws.plain(guesses, scores)
            
            response = f"Wow, it really took you {num_guesses} guess{'es' if num_guesses > 1 else ''}? Lmao."
            # response = plain
            await message.channel.send(response)

    await bot.process_commands(message)




# !!! BLOCKING !!! BLOCKING !!! BLOCKING !!! BLOCKING !!! BLOCKING !!! BLOCKING !!! BLOCKING
# Start the Discord bot.
bot.run(bot_token)
print('bot.py> Done!')