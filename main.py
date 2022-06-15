#!./env/bin/python3
import bot

#region Doin' your mom, doi-doin' your mom
# Here we mimic Wordle's "Word of the Day" (WOTD) function and
# use the same input data. 
########## W.I.P. ########## W.I.P. ########## W.I.P. ########## W.I.P. ##########

# import word_lists.HAX
# import time
# import datetime

# SEC_PER_DAY = 86400

# # GMT: Saturday, June 19, 2021 12:00:00 AM
# epoch_start = int(datetime.datetime(2021, 6, 19, 0, 0, 0, 0).timestamp())
# epoch_now   = int(time.time())
# index       = (epoch_now - epoch_start) // SEC_PER_DAY
# print(f"start = {epoch_start}\nnow = {epoch_now}\nindex = {index}")

# ko_dict = word_lists.HAX.load_ko()
# vals = list(ko_dict.values())
# print("wotd = ", vals[index])
#endregion


print("Starting bot...")
bot.run()