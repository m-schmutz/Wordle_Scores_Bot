from datetime import datetime
from typing import Tuple
from requests import get
from json import loads
from re import search, findall
from pickle import load, dump
from os.path import exists

# the last valid 5 letter word, this is used to locate the word list
LAST_VALID_WORD = 'zymic'

# paths to both pickle files that store word lists
WO_PATH = './lib/wordle_pickles/word_order.pkl'
VW_PATH = './lib/wordle_pickles/valid_words.pkl'

# gets the word of the day from the api endpoint
def get_wotd(dtime:datetime=datetime.now(), wrdl_num:bool=False) -> str|Tuple[str, int]:
    '''
    Returns word of the day\n
    ---
    #### If dtime parameter is left blank, the function will use the current day
    #### Otherwise datetime passed is used

    #### If wrdl_num is set to True, the function will return the wotd and the wordle number in a tuple
    
    '''
    # convert datetime to string in form YYYY-MM-DD
    date = dtime.strftime('%Y-%m-%d')
    
    # send get request for JSON data
    r = loads(get(f'https://www.nytimes.com/svc/wordle/v2/{date}.json').text)

    # if the caller wants the wordle number, return tuple
    if wrdl_num:
        return r['solution'], r['id']
    
    # parse and return solution field
    return r['solution']


# return the list of valid words
def get_valid_words() -> frozenset:
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


# retrieves the word banks from the wordle website javascript
def _get_word_banks() -> Tuple[list, frozenset]:
    # get the webpage source as text from the website
    web_source_txt = get('https://www.nytimes.com/games/wordle/index.html').text

    # extract the javascript file link from the page source
    js_file_link = search('https://www.nytimes.com/games-assets/v2/wordle.[\w]{40}.js', web_source_txt).group()

    # get the javascript file text from the link aquired in the previous step
    js_file_txt = get(js_file_link).text

    # get the banks from the javascript file
    banks = findall('\[((["][a-z]{5}["][,]?){50,})\]', js_file_txt)

    # split up the string by ',' to get each word by itself
    all_words = str(banks[0][0]).replace('\"', '').split(',')

    # slice out the word of the days
    word_order = all_words[all_words.index(LAST_VALID_WORD)+1:]

    # return the list of valid words and the set of valid words
    return word_order, frozenset(all_words)

    
# load in pickle file
def _load_pkl(path:str) -> frozenset|list:
    # load in set from pickle file and return
    with open(path, 'rb') as f:
        return load(f)


# store object as a pickle file
def _store_pkl(s:frozenset|list, path:str) -> None:
    # open the file path to write the pickle data
    with open(path, 'wb') as f:
        # write the pickled data to file_path
        dump(s, f)


# determine which files need to be created
def gen_files() -> bool:
    # check which pickles exist
    wo_exist = exists(WO_PATH)
    vw_exist = exists(VW_PATH)

    # check if both files exist. If they do exit function
    if wo_exist and vw_exist:
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
    