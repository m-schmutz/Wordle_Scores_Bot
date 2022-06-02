#!./../env/bin/python3
import requests
from datetime import datetime, timedelta, date
import re
import pickle
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
########################################################################################
# updates the stored data by requesting new data and storing it into the two files
def update_data():
    given_word = input("Enter today's known Wordle Word: ")
    if not(res(word_pattern, given_word)):
        print('Wordle Word must be five letter word lowercase')
        return 'wrong word format'
    # get the two word lists
    ko, wo = get_web_data()
    # #get ko_dict (date to word mappings)
    ko_dict = map_word_dates(given_word, ko)
    # #store the data into the two files
    store_data(ko_dict, wo)
    # # log update
    print('LOG: DATA UPDATED')
########################################################################################
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
########################################################################################
# return the word for a given date, passed in through search_date
# date string must be in form XXXX-XX-XX in order year-month-day
def get_word_by_date(search_date:str):
    #check that date is in correct form
    if not(res(date_pattern, search_date)):
        print('search_date needs to be in form XXXX-XX-XX (year-month-day)')
        return 'wrong input format'
    # load data from ko_dict
    ko_dict = load_ko()
    # get the word for the specified date
    word = ko_dict[search_date]
    #return the word
    return word
########################################################################################
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
########################################################################################
if __name__ == '__main__':
    update_data()

    word = get_todays_word()

    print(f'Today\'s word is: {word}')

    while 1:
        search_date = input('Enter date to search: ')
        prev = get_word_by_date
        print(f'word on {search_date} was: {prev}')