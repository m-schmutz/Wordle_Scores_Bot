from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from json import loads as JSONloads

options = FirefoxOptions()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options, service_log_path='./lib/geckodriver.log')

driver.get('https://www.nytimes.com/games/wordle/index.html')
# !!! DO NOT RUN !!! this literally consumed all of my memory. is it a bug? or do i misunderstand?
# wotd = driver.execute_script('var d = window.localStorage.getItem("nyt-wordle-state"); return JSON.parse(d["solution"])')
# !!! DO NOT RUN !!!
nyt_wordle_state = driver.execute_script('return window.localStorage.getItem("nyt-wordle-state")')
wotd = JSONloads(nyt_wordle_state)['solution']

print('Word of the Day:', wotd)