from typing import Tuple
from wordle import WordleScraper
from datetime import datetime, timedelta
import requests
import re
import pickle
import os

class WordLookup:
    '''
    WordLookup class. Provides an API for getting words and dates from the wordle website
    Words are stored in pickle files
    '''

    def __init__(self) -> None:
        # check if files need to be generated
        if not self.check_existing():
            # generate files and registry
            self.gen_files()

 
    def lookup_by_date(self, dtime:datetime) -> str:
        '''Takes in a datetime object and returns the word mapped at that date'''
        # load in the year dictionary from pickle file
        year_dict = self.load_object(dtime.year)

        # return the word at the datetime passed
        return year_dict[dtime]   

    
    def lookup_by_word(self, word:str) -> datetime:
        '''Takes in a word and returns the datetime object mapped at that word'''
        # load the word dictionary from pcilel file
        word_dict = self.load_object('reverse')

        # return datetime at word passed
        return word_dict[word]

  
    def get_valid_words(self) -> list:
        '''Returns the list of valid words retrieved from the website'''
        # load the valid_words list from pickle file
        valid_words = self.load_object('valid_words')

        # return the list
        return valid_words

 
    def get_word_index(self, word:str) -> int:
        '''Takes in a word and returns the index of the word in the word_order list'''
        # load the word_order list form the pickle file
        word_order = self.load_object('word_order')

        # return the index of the word
        return word_order.index(word)

  
    def _get_word_order(self) -> list[str]:
        word_order = self.load_object('word_order')

        return word_order

    ####################################################
    # methods for generating files

    def check_existing(self) -> bool:
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
            registry = self.load_object('registry')

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
            

    def get_word_banks(self) -> Tuple[list, list]:
        # get the webpage source as text from the website
        web_source_txt = requests.get('https://www.nytimes.com/games/wordle/index.html').text

        # extract the javascript file link from the page source
        js_file_link = re.search('https://www.nytimes.com/games-assets/v2/wordle.[\w]{40}.js', web_source_txt).group()

        # get the javascript file text from the link aquired in the previous step
        js_file_txt = requests.get(js_file_link).text

        # get the banks from the javascript file
        banks = re.findall('\[((["][a-z]{5}["][,]?){50,})\]', js_file_txt)

        # remove the banks returned from tuples and fix formatting
        word_order = banks[0][0].replace('"', '').split(',')
        valid_words = banks[1][0].replace('"', '').split(',')

        # return the two lists
        return word_order, valid_words


    def get_wotd(self) -> str:
        # create a wotd_scraper object. This will get the wotd on creation
        scraper = WordleScraper()

        # return the word of the day 
        return scraper._wotd


    def get_todays_date(self) -> datetime:
        # return todays date as a datetime object
        return datetime.now().date()


    def map_date_to_word(self, word_order:list) -> dict:
        # get todays date as a datetime object
        todays_date = self.get_todays_date()

        # get todays word of the day
        wotd = self.get_wotd()

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


    def map_word_to_date(self, d_to_w:dict) -> dict:
        # initialize new dictionary
        w_to_d = dict()

        # loop through d_to_w dictionary and reverse mapping
        for date, word in d_to_w.items():
            # map word to date
            w_to_d[word] = date

        # return dictionary
        return w_to_d


    def pkl_object(self, object:dict|list, file_prefix:str) -> None:
        # path for the pickled
        file_path = f'./lib/wordle_pickles/{file_prefix}.pkl'
        
        # open the file path to write the pickle data
        with open(file_path, 'wb') as f:
            
            # write the pickled data to file_path
            pickle.dump(object, f)


    def load_object(self, file_prefix:str) -> dict|list:
        # get the file path for the pickled data
        file_path = f'./lib/wordle_pickles/{file_prefix}.pkl'
        
        # open the pkl file
        with open(file_path, 'rb') as f:
            # load the pickled data
            object = pickle.load(f)

        # return the dictionary
        return object  


    def store_d_to_w(self, d_to_w:dict) -> list:
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
                self.pkl_object(temp_dict, curr_year)

                # add the file prefix to the registry list
                registry.append(str(curr_year))

                # clear the temp dictionary
                temp_dict.clear()

                # add the first entry for the new year
                temp_dict.update({date: word})
            
            # set curr_year to the year date
            curr_year = date.year

        # pickle last temp_dict
        self.pkl_object(temp_dict, curr_year)

        # add the file prefix to the registry list
        registry.append(str(curr_year))

        # return the registry list
        return registry


    def store_other(self, object:dict|list, prefix:str) -> str:
        # pickle the object
        self.pkl_object(object, prefix)

        # return the prefix after the object as been successfully stored
        return prefix


    def gen_files(self) -> None:
        # get the word lists from the wordle website
        word_order, valid_words = self.get_word_banks()

        # add the words in word_order to valid words
        # we found that the words in word_order are not contained in valid_words
        valid_words.extend(word_order)

        # sort list in alphabetical order
        valid_words.sort()

        # get the dictionary that maps dates to words
        d_to_w = self.map_date_to_word(word_order)

        # get the dictionary that maps words to dates
        w_to_d = self.map_word_to_date(d_to_w)

        # initialize registry list. This will store the prefixes of files so that
        # class can determine if needed files exist or not
        registry_list = list()

        # store the word_order list to files and add file prefixes to registry list
        registry_list.append(self.store_other(word_order, 'word_order'))

        # store the d_to_w dictionary to files and add file prefixes to registry list
        registry_list.extend(self.store_d_to_w(d_to_w))

        # store w_to_d dictionary to file and add file prefix to the registry list
        registry_list.append(self.store_other(w_to_d, 'reverse'))

        # store the valid words to file and add the file prefix to the registry list
        registry_list.append(self.store_other(valid_words, 'valid_words'))

        # write registry list to pickle file for restart
        self.pkl_object(registry_list, 'registry')