# import path from sys
from sys import path, exc_info
from __main__ import __file__
from os.path import basename

# add the lib directory so that python will search it for modules
path.append('./lib')

match basename(__file__):
    case 'run_bot.py':
        # imports required to run bot
        from random import randint
        from discord import Interaction, Attachment, app_commands
        from wordlebot import *
        from credentials import bot_token, server_id

    case 'setup.py':
        from env_setup import *

