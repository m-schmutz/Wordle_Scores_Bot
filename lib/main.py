from wordle import Bot
from credentials import bot_token, server_id

bot = Bot(bot_token, server_id)
bot.run()
