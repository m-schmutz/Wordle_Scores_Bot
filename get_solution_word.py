#!./env/bin/python3
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

SOLUTION_OFFSET = 105
END_OF_WORD = 110

firefox_options = Options()
firefox_options.add_argument('--headless')
 

wd = webdriver.Firefox(options=firefox_options)

wd.get("https://www.nytimes.com/games/wordle/index.html")
r = wd.execute_script("return window.localStorage.getItem('nyt-wordle-state')")
# print(r)
# index = r.find("solution")
# print(index)

solution = r[SOLUTION_OFFSET:END_OF_WORD]

print(f'Today\'s Word is: {solution}')
 