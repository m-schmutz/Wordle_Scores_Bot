from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from os import stat
from datetime import datetime

WOTD_PATH = './lib/wotd.txt'

# Firefox Browser Options
options = webdriver.FirefoxOptions()
options.headless = True
options.page_load_strategy = 'eager'

# Firefox Service Object
driverService = Service(log_path='./lib/geckodriver.log')

# Webscrapes the official Wordle webpage for the WOTD
def _scrape_wotd():
    # Create the Selenium webdriver
    driver = webdriver.Firefox(options=options, service=driverService)

    # GET webpage and parse localStorage for WOTD.
    driver.get('https://www.nytimes.com/games/wordle/index.html')
    nyt_wordle_state:str = driver.execute_script('return window.localStorage.getItem("nyt-wordle-state")')
    wotd = nyt_wordle_state.split('"solution":"')[1][:5] # about twice as fast as json.loads()

    # WILL LEAK MEMORY IF NOT CLOSED
    driver.quit()

    return wotd

# Updates local data and returns the WOTD.
def _update():
    # Webscrape for WOTD.
    wotd = _scrape_wotd()

    # Write WOTD to file.
    with open(WOTD_PATH, 'w') as f:
        f.write(wotd)

    return wotd

# Returns the WOTD.
def wotd():
    # Get timestamp of last modification to data.
    # This should only raise an exception initially, when the data has not yet been initialized.
    try: file_modified_epoch = stat(WOTD_PATH).st_mtime
    except FileNotFoundError:
        return _update()

    # If WOTD is old, update and return the new WOTD.
    today = datetime.now().date()
    day_modified = datetime.fromtimestamp(file_modified_epoch).date()
    if (today > day_modified):
        return _update()

    # WOTD on file is valid, so return it.
    with open(WOTD_PATH, 'r') as f:
        return f.read()
