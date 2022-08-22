#!./venv/bin/python3.10
from lib.word_lookup import WordLookup
from datetime import datetime

wait = input('Warning, script output will reveal todays word. Press Enter to continue...')


wl = WordLookup()


date = datetime.now().date()

word = wl.lookup_by_date(date)

print(f'word on {date.isoformat()}: {word}')

print(f'{word} was word of the day on {wl.lookup_by_word(word)}')


ind = wl.get_word_index(word)

postfixes = {1: 'st', 2: 'nd', 3: 'rd'}

last_digit = int(str(ind)[-1])

try:
    postfix = postfixes[last_digit]

except KeyError:
    postfix = 'th'

print(f'{word} is the {ind + 1}{postfix} wordle')