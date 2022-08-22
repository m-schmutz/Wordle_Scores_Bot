#!/bin/python3.10
import requests
from credentials import api_headers
import json

DEF_TEMPLATE = 'https://wordsapiv1.p.rapidapi.com/words/{word}/definitions'

FREQ_TEMPLATE = 'https://wordsapiv1.p.rapidapi.com/words/{word}/frequency'

EXAM_TEMPLATE = 'https://wordsapiv1.p.rapidapi.com/words/{word}/examples'


class WordInfo:
    def __init__(self, wotd:str) -> None:

        # store the word that all the info will be for
        self.word = wotd

        # get json data for the definition(s)
        def_json = json.loads(requests.get(DEF_TEMPLATE.format(word = wotd), headers=api_headers).text)
        
        # get json data for the frequency 
        freq_json = json.loads(requests.get(FREQ_TEMPLATE.format(word = wotd), headers=api_headers).text)

        # get the json data for examples
        exam_json = json.loads(requests.get(EXAM_TEMPLATE.format(word = wotd), headers=api_headers).text)
        
        # store the definitions of word sorted by part of speech
        self.definitions = self.parse_definitions(def_json['definitions'])

        # store the frequency of the word on average per million words
        self.per_million:float = freq_json['frequency']['perMillion']

        # store examples of the word in a sentence
        self.examples:list = exam_json['examples']
   
    @staticmethod
    def parse_definitions(json_defs:list) -> dict[str, list[str]]:
        # initialize the dictionary
        grouped_defs:dict[str, list] = dict()

        # loop through each definition and part of speech dicitonary
        for entry in json_defs:
            # extract definition and part of speech
            definition:str = entry['definition']
            part_of_speech:str = entry['partOfSpeech']

            # try to append definition to the list mapped to part of speech
            try:
                grouped_defs[part_of_speech].append(definition)

            # else make new list mapped at part of speech 
            except KeyError:
                grouped_defs[part_of_speech] = [definition]

        # return the dictionary
        return grouped_defs


    def print_info(self):
        print('=============')
        print(f'=== {self.word} ===')
        print('=============')
        print()
        print('Definitions: ')
        for part, defs in self.definitions.items():
            print(f'    {part}:')
            for d in defs:
                print(f'\t- {d}')
        
        print()
        print(f'Examples of Usage:')
        for e in self.examples:
            print(f'\t- {e}')

        print()
        print(f'Average frequency per 1 million words: {self.per_million}')


    def __str__(self) -> str:
        return f'{self.definitions = }\n{self.per_million = }\n{self.examples}'


wi = WordInfo('waste')

wi.print_info()