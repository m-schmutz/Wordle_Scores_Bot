import re
import requests

url = 'https://www.nytimes.com/games-assets/v2/wordle.4f3b14d90b6576db06370f9e6067f569ce52a46f.js'
results = re.findall('\[((["][a-z]{5}["][,]?){50,})\]', requests.get(url).text)
word_order = results[0][0].replace('"', '').split(',')
valid_words = results[1][0].replace('"', '').split(',')

# Should be 2309 and 10665, respectively
print(len(word_order), len(valid_words))