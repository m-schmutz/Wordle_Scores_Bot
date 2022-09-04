# import path from sys
from sys import path

# add the lib directory so that python will search it for modules
path.append('./lib')

# import needed classes from wordle.py
from random import randint
from discord import Interaction, Attachment, app_commands
from wordle import SubmissionEmbed, InvalidGame, WordleBot, DoubleSubmit, LinkView
from credentials import bot_token, server_id