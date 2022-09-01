from typing import Tuple
from lib.wordle import WordleScraper
from datetime import datetime, timedelta
from requests import get
from re import search, findall
import pickle
import os

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
        # load in the year dictionary from pickle file
        year_dict = self._load_object(dtime.year)

        # return the word at the datetime passed
        return year_dict[dtime]   

    
    def lookup_by_word(self, word:str) -> datetime:
        '''Takes in a word and returns the datetime object mapped at that word'''
        # load the word dictionary from pcilel file
        word_dict = self._load_object('reverse')

        # return datetime at word passed
        return word_dict[word]

  
    def get_valid_words(self) -> list:
        '''Returns the list of valid words retrieved from the website'''
        # load the valid_words list from pickle file
        valid_words = self._load_object('valid_words')

        # return the list
        return valid_words

 
    def get_word_index(self, word:str) -> int:
        '''Takes in a word and returns the index of the word in the word_order list'''
        # load the word_order list form the pickle file
        word_order = self._load_object('word_order')

        # return the index of the word
        return word_order.index(word)

  
    def _get_word_order(self) -> list[str]:
        word_order = self._load_object('word_order')

        return word_order

    ####################################################
    # methods for generating files

    def _check_existing(self) -> bool:
        # get the parent directory path
        parent_dir = './lib/wordle_pickles/{prefix}.pkl'[:20]

        # check if the parent directory exists
        if not os.path.exists(parent_dir):
            # if it does not exist, create it
            os.mkdir(parent_dir)

            # return false so that files are created
            return False

        # get the registry file path
        registry_path = './lib/wordle_pickles/registry.pkl'
    
        # else check if the registry file exists
        if os.path.exists(registry_path):

            # load the registry list
            registry = self._load_object('registry')

            # loop through each item in the registry list
            for file_prefix in registry:

                # check if path exists to pkl file
                if not os.path.exists(f'./lib/wordle_pickles/{file_prefix}.pkl'):

                    # if a file does not exist, need to generate files
                    return False
            
            # else return true as all files exist
            return True
        
        # if directory exists but registry does not, return false and create files
        else: 
            return False
            

    def _get_word_banks(self) -> Tuple[list, list]:
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


    def _get_wotd(self) -> str:
        # create a wotd_scraper object. This will get the wotd on creation
        scraper = WordleScraper()

        # return the word of the day 
        return scraper._wotd


    def _get_todays_date(self) -> datetime:
        # return todays date as a datetime object
        return datetime.now().date()


    def _map_date_to_word(self, word_order:list) -> dict[datetime, str]:
        # get todays date as a datetime object
        todays_date = self._get_todays_date()

        # get todays word of the day
        wotd = self._get_wotd()

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


    def _map_word_to_date(self, d_to_w:dict) -> dict[str, datetime]:
        # initialize new dictionary
        w_to_d = dict()

        # loop through d_to_w dictionary and reverse mapping
        for date, word in d_to_w.items():
            # map word to date
            w_to_d[word] = date

        # return dictionary
        return w_to_d


    def _pkl_object(self, object:dict|list, file_prefix:str) -> None:
        # path for the pickled
        file_path = f'./lib/wordle_pickles/{file_prefix}.pkl'
        
        # open the file path to write the pickle data
        with open(file_path, 'wb') as f:
            
            # write the pickled data to file_path
            pickle.dump(object, f)


    def _load_object(self, file_prefix:str) -> dict|list:
        # get the file path for the pickled data
        file_path = f'./lib/wordle_pickles/{file_prefix}.pkl'
        
        # open the pkl file
        with open(file_path, 'rb') as f:
            # load the pickled data
            object = pickle.load(f)

        # return the dictionary
        return object  


    def _store_d_to_w(self, d_to_w:dict[datetime, str]) -> list:
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
                self._pkl_object(temp_dict, curr_year)

                # add the file prefix to the registry list
                registry.append(str(curr_year))

                # clear the temp dictionary
                temp_dict.clear()

                # add the first entry for the new year
                temp_dict.update({date: word})
            
            # set curr_year to the year date
            curr_year = date.year

        # pickle last temp_dict
        self._pkl_object(temp_dict, curr_year)

        # add the file prefix to the registry list
        registry.append(str(curr_year))

        # return the registry list
        return registry


    def _store_other(self, object:dict|list, prefix:str) -> str:
        # pickle the object
        self._pkl_object(object, prefix)

        # return the prefix after the object as been successfully stored
        return prefix


    def _gen_files(self) -> None:
        # get the word lists from the wordle website
        word_order, valid_words = self._get_word_banks()

        # add the words in word_order to valid words
        # we found that the words in word_order are not contained in valid_words
        valid_words.extend(word_order)

        # sort list in alphabetical order
        valid_words.sort()

        # get the dictionary that maps dates to words
        d_to_w = self._map_date_to_word(word_order)

        # get the dictionary that maps words to dates
        w_to_d = self._map_word_to_date(d_to_w)

        # initialize registry list. This will store the prefixes of files so that
        # class can determine if needed files exist or not
        registry_list = list()

        # store the word_order list to files and add file prefixes to registry list
        registry_list.append(self._store_other(word_order, 'word_order'))

        # store the d_to_w dictionary to files and add file prefixes to registry list
        registry_list.extend(self._store_d_to_w(d_to_w))

        # store w_to_d dictionary to file and add file prefix to the registry list
        registry_list.append(self._store_other(w_to_d, 'reverse'))

        # store the valid words to file and add the file prefix to the registry list
        registry_list.append(self._store_other(valid_words, 'valid_words'))

        # write registry list to pickle file for restart
        self._pkl_object(registry_list, 'registry')