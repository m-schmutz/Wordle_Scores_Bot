#!../venv/bin/python3.10
from sys import path
path.append('../')
from lib.wotd import get_wotd, get_valid_words, get_word_order
from datetime import datetime


print(get_wotd(datetime.now()))


