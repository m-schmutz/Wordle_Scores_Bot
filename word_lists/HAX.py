#!./../env/bin/python3
import requests
from datetime import datetime, timedelta, date
import re
import pickle
########################################################################################
#region "constants"
########################################################################################
# OFFSET is used to remove the first 3 letters of the matching string ('ko=' and 'wo=')
OFFSET = 3

# ko pattern is the reg-ex that will find the first word list in the main.js file
ko_pattern = r'ko=\[((\"[a-z]{5}\",?)+)\]'

# wo pattern is the reg-ex that will find the second word list in the main.js file
wo_pattern = r'wo=\[((\"[a-z]{5}\",?)+)\]'

# date_pattern is reg-ex pattern that search_dates must adhere to 
date_pattern = r'[0-9]{4}-[0-9]{2}-[0-9]{2}'

# word_pattern is reg-ex that defines a 5 letter word
word_pattern = r'[a-z]{5}'

# re.search() function 
res = re.search
########################################################################################
#endregion
########################################################################################

########################################################################################
#region get__web_data()
########################################################################################
# requests from www.nytimes.com for the main.js file which contains the two word lists
# and returns them as comma delimited lists
def get_web_data():
    # use requests to get the entire file
    req = requests.get('https://www.nytimes.com/games/wordle/main.9622bc55.js')

    # decode output
    file = req.content.decode()

    # get the span of each string using a regular expression search
    ko_start, ko_end = res(ko_pattern, file).span()
    wo_start, wo_end = res(wo_pattern, file).span()

    # get both strings of words by extracting from file. Removes 'ko=' and 'ow='.
    ko_str, wo_str = file[ko_start + OFFSET:ko_end], file[wo_start + OFFSET:wo_end]  

    # strips off '[]' and deletes double quotes
    ko_str = ko_str.strip('[]')
    ko_str = ko_str.replace('"', '')

    wo_str = wo_str.strip('[]')
    wo_str = wo_str.replace('"', '')

    # split up each string into a list using the comma as a delimiter
    ko = list(ko_str.split(','))
    wo = list(wo_str.split(','))

    # return the two lists
    return ko, wo
########################################################################################
#endregion
########################################################################################

########################################################################################
#region map_word_dates()
########################################################################################
# map each word in the ko list to its corresponding date
def map_word_dates(todays_word:str, ko:list):
    # initialize ko_dict, a dictionary mapping each date to a word
    ko_dict = dict()

    # get the index of todays word in the ko list
    # this is done so that we have a reference point to start at (todays date maps to todays word)
    ref_index = ko.index(todays_word)

    # get todays date
    ref_date = datetime.now().date()

    # delta is one day
    delta = timedelta(days=1)

    # find the date that refers to the first word
    first_date = ref_date - delta * ref_index

    # set date to start at the start_date
    date = first_date

    # for each word in the ko list
    for word in ko:
        # map the word to the corresponding date
        ko_dict[str(date)] = word

        # increment date by one day
        date += delta
        
    # return the dictionary
    return ko_dict
########################################################################################
#endregion
########################################################################################

########################################################################################
#region store_data()
########################################################################################
# this will take the data from the two lists and store them in pickle files
def store_data(ko_dict, wo):
    # open ko.pkl file
    with open('./ko.pkl', 'wb') as ko_f:
        # put ko_dict date into the file
        pickle.dump(ko_dict, ko_f)
    # open wo.pkl file
    with open('./wo.pkl', 'wb') as wo_f:
        # put wo data into the file
        pickle.dump(wo, wo_f)
########################################################################################
#endregion
########################################################################################

########################################################################################
#region update_data()
########################################################################################
# update to raise exception
# updates the stored data by requesting new data and storing it into the two files
def update_data():
    given_word = input("Enter today's known Wordle Word: ")
    if not(res(word_pattern, given_word)):
        print('Wordle Word must be five letter word lowercase')
        raise Exception('Invalid word')
    # get the two word lists
    ko, wo = get_web_data()
    # #get ko_dict (date to word mappings)
    ko_dict = map_word_dates(given_word, ko)
    # #store the data into the two files
    store_data(ko_dict, wo)
    # # log update
    print('LOG: DATA UPDATED')
########################################################################################
#endregion
########################################################################################

########################################################################################
#region load_ko()
########################################################################################
# load the ko data to get the dictionary
def load_ko():
    # open ko_dict file
    with open('./ko.pkl', 'rb') as ko_f:
        # load the data into a dictionary
        ko_dict = pickle.load(ko_f)
    # return the dictionary
    return ko_dict
########################################################################################
#endregion
########################################################################################

########################################################################################
#region search_by_date()
########################################################################################
# return the word for a given date, passed in through search_date
# date string must be in form XXXX-XX-XX in order year-month-day

#update to raise exception

def search_by_date(search_date:str):
    #check that date is in correct form
    if not(res(date_pattern, search_date)):
        print('search_date needs to be in form XXXX-XX-XX (year-month-day)')
        raise Exception("Wrong Format")
    # load data from ko_dict
    ko_dict = load_ko()
    # get the word for the specified date
    try:
        word = ko_dict[search_date]
    except:
        print('date not mapped to word')
    #return the word
    return word
########################################################################################
#endregion
########################################################################################

########################################################################################
#region get_todays_word()
########################################################################################
# returns todays date
def get_todays_word():
    # get todays date
    today = str(date.today())
    # load ko_dict data
    ko_dict = load_ko()
    # get word that corresponds to todays date
    word = ko_dict[today]
    # return word of the day
    return word
########################################################################################
#endregion
########################################################################################

########################################################################################
#region search_by_word()
########################################################################################
# write function to search by word and get date
def search_by_word():
    search_word = input("Enter word to search: ")
    if not(res(word_pattern, search_word)):
        print('Wordle Word must be five letter word lowercase')
        raise Exception('Invalid word')
    ko_dict = load_ko()
    dates = ko_dict.keys()
    for date in dates:
        if ko_dict[date] == search_word:
            return date
    else:
        return 'word not in wordlist'

########################################################################################
#endregion
########################################################################################

########################################################################################

# write function to store words of the month

if __name__ == '__main__':
    update_data()

    word = get_todays_word()

    print(f'Today\'s word is: {word}')
