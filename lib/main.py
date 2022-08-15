from wordle import Bot
from credentials import bot_token, server_id

bot = Bot(bot_token, server_id)
bot.run()



# d = dict(
#     (k,v)
#     for k,v in zip(
#         range(1,7),
#         '10 20 30 40 50 60'.split()))
# print(d)

# s = ' '.join(d.values())
# print(f'"{s}"')



# import requests
# words = requests.get('https://raw.githubusercontent.com/dwyl/english-words/master/words.txt').text.split('\n')
# words5 = [
#     w
#     for w in words
#     if len(w) == 5
#     and all(c in 'abcdefghijklmnopqrstuvwxyz' for c in w)]

# print(f'{len(words) = }\n{len(words5) = }')
