#!./venv/bin/python3
from lib.word_lookup import WordLookup
from datetime import datetime

wl = WordLookup()

print(wl.lookup_by_date(datetime.now().date()))
print(wl.lookup_by_word('poker'))
