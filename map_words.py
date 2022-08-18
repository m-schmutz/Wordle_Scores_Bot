#!./venv/bin/python3
from lib.word_lookup import WordLookup
from datetime import datetime

wl = WordLookup()

date = datetime.fromisoformat('2022-08-15').date()

word = wl.lookup_by_date(date)

print(f'word on {date.isoformat()}: {word}')

print(f'{word} was word of the day in {wl.lookup_by_word(word)}')
