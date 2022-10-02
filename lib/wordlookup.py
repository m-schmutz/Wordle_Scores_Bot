from datetime import datetime
from requests import get
from re import search, findall
from pickle import load, dump
from os.path import exists
from wotd import get_wotd
from typing import Tuple

################################################################################################################################################
# WordLookup class:
# used to look up the day that a word was wotd or what the wotd is on a specific date
################################################################################################################################################
class WordLookup:
    '''
    WordLookup class. Provides an API for getting words and dates from the wordle website
    Words are stored in pickle files
    #### Methods
    ---
    - lookup_by_date(): Given a datetime object, the method returns the word that is mapped at that date
    - lookup_by_word(): Given a word, the method will return the datetime object that is mapped at that word
    - get_valid_words(): Method returns the list of valid words that wordle will accept as guesses
    - get_word_index(): Given a word, the method will return the index of the word contained in word_order
    '''

    def __init__(self) -> None:
        # check if files need to be generated
        if not self._check_existing():
            # generate files and registry
            self._gen_files()

 
    def lookup_by_date(self, dtime:datetime) -> str:
        '''Takes in a datetime object and returns the word mapped at that date'''
        return get_wotd(dtime)

    
    def get_todays_word(self) -> str:
        # get today's date as a datetime object
        today = datetime.now().date()

        # return the word mapped to todays date
        return get_wotd(today)

  
    def get_valid_words(self) -> set:
        '''Returns the list of valid words retrieved from the website'''
        # load the valid_words list from pickle file
        valid_words = self._load_object('valid_words')

        # return as a set
        return set(valid_words)


    def _get_word_order(self) -> list[str]:
        word_order = self._load_object('word_order')

        return word_order

    ####################################################
    # methods for generating files

    @staticmethod
    def _check_existing() -> bool:
       return exists('./lib/wordle_pickles/word_order.pkl') and exists('./lib/wordle_pickles/valid_words.pkl')
            
    @staticmethod
    def _get_word_banks() -> Tuple[list, list]:
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
        valid_words = banks[1][0].replace('"', '').split(',')

        # return the two lists
        return word_order, valid_words

    @staticmethod
    def _pkl_object(object:dict|list, file_prefix:str) -> None:
        # path for the pickled
        file_path = f'./lib/wordle_pickles/{file_prefix}.pkl'
        
        # open the file path to write the pickle data
        with open(file_path, 'wb') as f:
            
            # write the pickled data to file_path
            dump(object, f)

    @staticmethod
    def _load_object(file_prefix:str) -> dict|list:
        # get the file path for the pickled data
        file_path = f'./lib/wordle_pickles/{file_prefix}.pkl'
        
        # open the pkl file
        with open(file_path, 'rb') as f:
            # load the pickled data
            object = load(f)

        # return the dictionary
        return object  


    def _gen_files(self) -> None:
        # get the word lists from the wordle website
        word_order, valid_words = self._get_word_banks()
        # add the words in word_order to valid words
        # we found that the words in word_order are not contained in valid_words
        valid_words.extend(word_order)

        # sort list in alphabetical order
        valid_words.sort()

        # store both lists 
        self._pkl_object(word_order, 'word_order')

        self._pkl_object(valid_words, 'valid_words')
