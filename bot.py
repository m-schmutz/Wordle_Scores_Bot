#!./env/bin/python3

# https://discordpy.readthedocs.io/en/stable/api.html
import discord
from discord.ext import commands
import credentials

import wordle_image_processing as wip
import wordle_scoring as ws
import constants as const

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

# @bot.command(name="kill")
# async def kill(context):
#     fn = "./debug_images_dump/yes_honey.png"
#     with open(fn, "rb") as fh:
#         f = discord.File(fh, filename=fn)

#     await context.send(file=f)
#     quit("Bot killed.")


@bot.command(name="link")
async def link(context):
    file    = discord.File( f"./{const.EMBED_IMG_NAME}" )
    embed   = discord.Embed(
        color       = const.EMBED_COLOR,
        title       = const.EMBED_TITLE,
        url         = const.EMBED_URL,
        description = const.EMBED_DESC )

    embed.set_image( url=f"attachment://{const.EMBED_IMG_NAME}" )

    await context.send(file=file, embed=embed)
    return

@bot.event
async def on_message(message):
    # Don't reply to self
    if message.author == bot.user:
        return

    # If message contains attachments...
    elif message.attachments:
        for att in message.attachments:
            img = await att.read()
            guesses = wip.get_guesses(img)
            num_guesses = len(guesses)
            # scores = ws.score_game(guesses, guesses[-1])
            # plain = ws.plain(guesses, scores)
            
            response = f"Wow, it really took you {num_guesses} guess{'es' if num_guesses > 1 else ''}? Lmao."
            # response = plain
            await message.channel.send(response)

    await bot.process_commands(message)


def run():
    bot.run(credentials.bot_token)