# import path from sys
from sys import path

# add the lib directory so that python will search it for modules
path.append('./lib')

# import needed classes from wordle.py
from wordle import WordInfo, WordLookup, WordleBot