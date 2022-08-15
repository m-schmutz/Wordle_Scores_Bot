from typing import Tuple, Union
from .wordle import _wotdScraper
from datetime import datetime, timedelta
import requests
import re
import pickle
import os

WEBSITE_LINK = 'https://www.nytimes.com/games/wordle/index.html'

FILE_RE = 'https://www.nytimes.com/games-assets/v2/wordle.[\w]{40}.js'

BANK_RE = '\[((["][a-z]{5}["][,]?){50,})\]'

TEMPLATE_PATH = './lib/wordle_pickles/{prefix}.pkl'

def get_word_banks() -> Tuple[list, list]:
    # get the webpage source as text from the website
    web_source_txt = requests.get('https://www.nytimes.com/games/wordle/index.html').text

    # extract the javascript file link from the page source
    js_file_link = re.search(FILE_RE, web_source_txt).group()

    # get the javascript file text from the link aquired in the previous step
    js_file_txt = requests.get(js_file_link).text

    # get the banks from the javascript file
    banks = re.findall(BANK_RE, js_file_txt)

    # remove the banks returned from tuples and fix formatting
    word_order = banks[0][0].replace('"', '').split(',')
    valid_words = banks[1][0].replace('"', '').split(',')

    # return the two lists
    return word_order, valid_words


def get_wotd() -> str:
    # create a wotd_scraper object. This will get the wotd on creation
    scraper = _wotdScraper()

    # return the word of the day 
    return scraper._wotd


def get_todays_date() -> datetime:
    # return todays date as a datetime object
    return datetime.now().date()


def map_date_to_word(word_order:list) -> dict:
    # get todays date as a datetime object
    todays_date = get_todays_date()

    # get todays word of the day
    wotd = get_wotd()

    # initialize timedelta to 1 day
    delta = timedelta(days=1)

    # get the index of todays word
    wotd_index = word_order.index(wotd)

    # find the date corresponding to the first 
    starting_date = todays_date - (delta * (wotd_index))

    # datetime object that will be used for mapping
    map_date = starting_date

    # initialize the dictionary to hold the mappings
    d_to_w = dict()

    # loop through each word in the word_order list
    for word in word_order:

        # map the word to its corresponding date
        d_to_w[map_date] = word

        # increment the date for the next word
        map_date += delta

    # return the mapped dictionary
    return d_to_w


def map_word_to_date(d_to_w:dict) -> dict:
    # initialize new dictionary
    w_to_d = dict()

    # loop through d_to_w dictionary and reverse mapping
    for date, word in d_to_w.items():
        # map word to date
        w_to_d[word] = date

    # return dictionary
    return w_to_d


def pkl_object(object:Union[dict, list], file_prefix):
    # path for the pickled
    file_path = TEMPLATE_PATH.format(prefix = file_prefix)
    
    # open the file path to write the pickle data
    with open(file_path, 'wb') as f:
        
        # write the pickled data to file_path
        pickle.dump(object, f)


def load_object(file_prefix) -> Union[dict, list]:
    # get the file path for the pickled data
    file_path = TEMPLATE_PATH.format(prefix = file_prefix)
    
    # open the pkl file
    with open(file_path, 'rb') as f:
        # load the pickled data
        object = pickle.load(f)

    # return the dictionary
    return object  


def check_existing():
    # get the parent directory path
    parent_dir = TEMPLATE_PATH[:20]

    # check if the parent directory exists
    if not os.path.exists(parent_dir):
        # if it does not exist, create it
        os.mkdir(parent_dir)

        # return false so that files are created
        return False

    # get the registry file path
    registry_path = TEMPLATE_PATH.format(prefix = 'registry')
 
    # else check if the registry file exists
    if os.path.exists(registry_path):

        # load the registry list
        registry = load_object('registry')

        # loop through each item in the registry list
        for file_prefix in registry:

            # check if path exists to pkl file
            if not os.path.exists(TEMPLATE_PATH.format(prefix = file_prefix)):

                # if a file does not exist, need to generate files
                return False
        
        # else return true as all files exist
        return True
    
    # if directory exists but registry does not, return false and create files
    else: 
        return False


def store_d_to_w(d_to_w:dict) -> list:
    # for typing stuff
    date:datetime

    # registry list to store file prefixes
    registry = list()

    # initialize the dictionary
    temp_dict = dict()

    # get the starting current year. This is used check when we are done with the 
    curr_year = list(d_to_w.keys())[0].year

    # loop through each mapping in the d_to_w dictionary
    for date, word in d_to_w.items():

        # check if the year of the current date matches the date of the previous
        if date.year == curr_year:
            
            # if in same year, add mapping to temp dictionary
            temp_dict.update({date: word})

        # else current date is in the next year, dump the current temp dictionary and start again with new year
        else:
            # pkl the temp dictionary
            pkl_object(temp_dict, curr_year)

            # add the file prefix to the registry list
            registry.append(str(curr_year))

            # clear the temp dictionary
            temp_dict.clear()

            # add the first entry for the new year
            temp_dict.update({date: word})
        
        # set curr_year to the year date
        curr_year = date.year

    # pickle last temp_dict
    pkl_object(temp_dict, curr_year)

    # add the file prefix to the registry list
    registry.append(str(curr_year))

    # return the registry list
    return registry


def store_w_to_d(w_to_d:dict) -> str:
    # prefix for pkl file containing reverse dictionary
    file_prefix = 'reverse'

    # store the pickled object
    pkl_object(w_to_d, file_prefix)

    # return the file_prefix
    return file_prefix


def store_valid_words(valid_words:list):
    # prefix for pkl file containing reverse dictionary
    file_prefix = 'valid_words'

    # store the pickled object
    pkl_object(valid_words, file_prefix)

    # return the file_prefix
    return file_prefix


def gen_files():
    # get the word lists from the wordle website
    word_order, valid_words = get_word_banks()

    # get the dictionary that maps dates to words
    d_to_w = map_date_to_word(word_order)

    # get the dictionary that maps words to dates
    w_to_d = map_word_to_date(d_to_w)

    # initialize registry list. This will store the prefixes of files so that
    # class can determine if needed files exist or not
    registry_list = list()

    # store the d_to_w dictionary to files and add file prefixes to registry list
    registry_list.extend(store_d_to_w(d_to_w))

    # store w_to_d dictionary to file and add file prefix to the registry list
    registry_list.append(store_w_to_d(w_to_d))

    # store the valid words to file and add the file prefix to the registry list
    registry_list.append(store_valid_words(valid_words))

    # write registry list to pickle file for restart
    pkl_object(registry_list, 'registry')


class WordLookup:
    '''
    WordLookup class. Provides an API for getting words and dates from the wordle website
    Words are stored in pickle files
    '''

    def __init__(self) -> None:
        # check if files need to be generated
        if not check_existing():
            # generate files and registry
            gen_files()


    def lookup_by_date(self, dtime:datetime) -> str:
        '''Takes in a datetime object and returns the word mapped at that date'''
        # load in the year dictionary from pickle file
        year_dict = load_object(dtime.year)

        # return the word at the datetime passed
        return year_dict[dtime]   


    def lookup_by_word(self, word:str) -> datetime:
        '''Takes in a word and returns the datetime object mapped at that word'''
        # load the word dictionary from pcilel file
        word_dict = load_object('reverse')

        # return datetime at word passed
        return word_dict[word]


    def get_valid_words(self) -> list:
        '''Returns the list of valid words retrieved from the website'''
        # load the valid_words list from pickle file
        valid_words = load_object('valid_words')

        # return the list
        return valid_words