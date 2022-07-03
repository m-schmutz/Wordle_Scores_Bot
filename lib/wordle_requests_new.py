from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import json

options = FirefoxOptions()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options)
driver.get('https://www.nytimes.com/games/wordle/index.html')
var = driver.execute_script('return window.localStorage.getItem("nyt-wordle-state")')
wotd = json.loads(var)['solution']
print(f'The WOTD is \'{wotd}\'')