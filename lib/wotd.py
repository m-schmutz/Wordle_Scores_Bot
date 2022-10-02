from datetime import datetime
from typing import Tuple
from requests import get
from json import loads
from re import search, findall
from pickle import load, dump
from os.path import exists

WO_PATH = './lib/wordle_pickles/word_order.pkl'

VW_PATH = './lib/wordle_pickles/valid_words.pkl'

# gets the word of the day from the api endpoint
def get_wotd(dtime:datetime, count:bool=False) -> str:
    '''
    Returns word of the day\n
    If count is true returns wotd and count in tuple:\n
    get_wotd(<dtime>, count=True) -> (<wotd>, <count>)
    '''
    # convert datetime to string in form YYYY-MM-DD
    date = dtime.strftime('%Y-%m-%d')
    
    # send get request for JSON data
    r = loads(get(f'https://www.nytimes.com/svc/wordle/v2/{date}.json').text)

    if count:
        return r['solution'], r['id']
    
    # parse and return solution field
    return r['solution']


# return the list of valid words
def get_valid_words() -> set:
    # assert that the valid words pickle exists
    assert(exists(VW_PATH))
    # return the set
    return _load_pkl(VW_PATH)


# return the word order list
def get_word_order() -> list:
    # assert that the valid words pickle exists
    assert(exists(WO_PATH))
    # return the set
    return _load_pkl(WO_PATH)


# gets the word banks from the wordle website javascript
def _get_word_banks() -> Tuple[list, set]:
    # get the webpage source as text from the website
    web_source_txt = get('https://www.nytimes.com/games/wordle/index.html').text

    # extract the javascript file link from the page source
    js_file_link = search('https://www.nytimes.com/games-assets/v2/wordle.[\w]{40}.js', web_source_txt).group()

    # get the javascript file text from the link aquired in the previous step
    js_file_txt = get(js_file_link).text

    # get the banks from the javascript file
    banks = findall('\[((["][a-z]{5}["][,]?){50,})\]', js_file_txt)

    # remove the banks returned from tuples and fix formatting
    word_order = banks[0][0].replace('"', '').split(',')
    valid_words = set(banks[1][0].replace('"', '').split(','))

    # return the two lists as sets
    return word_order, valid_words.update(word_order)


# load in pickle file
def _load_pkl(path:str) -> set:
    # load in set from pickle file and return
    with open(path, 'rb') as f:
        return load(f)


# store object as a pickle file
def _store_pkl(s:set, path:str) -> None:
        # open the file path to write the pickle data
        with open(path, 'wb') as f:
            # write the pickled data to file_path
            dump(s, f)


# determine which files need to be created
def gen_files() -> bool:
    wo_exist = exists(WO_PATH)
    vw_exist = exists(VW_PATH)
    # check if both files exist. If they do exit function
    if not wo_exist and vw_exist:
        # files were not generated
        return False
    
    # grab word lists from wordle game assets
    word_order, valid_words = _get_word_banks()
    
    # store the word_order if the pickle does not exist
    if not wo_exist:
        _store_pkl(word_order, WO_PATH)

    # store the valid_words if the pickle does not exist
    if not vw_exist:
        _store_pkl(valid_words, VW_PATH)
    
    # files were generated
    return True
        
