# import path from sys
from sys import path
from __main__ import __file__

# add the lib directory so that python will search it for modules
path.append('./lib')

# check that this file is not being imported from the setup.py file
if __file__[-8:] != 'setup.py':
    # import needed classes from wordle.py
    from random import randint
    from discord import Interaction, Attachment, app_commands
    from wordle import *
    from credentials import bot_token, server_id

# if it is, only import env_setup objects
else:
    from env_setup import *