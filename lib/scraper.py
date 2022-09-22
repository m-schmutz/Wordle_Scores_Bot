from datetime import datetime
from atexit import register
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
################################################################################################################################################
# WOTDScraper class:
# used to get the wotd from the wordle website using selenium webscraping
################################################################################################################################################
class WOTDScraper:
    """Keeps track of the Word of the Day. Uses Selenium to scrape the NYTimes Wordle webpage."""

    def __init__(self) -> None:
        opts = webdriver.FirefoxOptions()
        opts.headless = True
        opts.page_load_strategy = 'eager'
        serv = Service(log_path='./lib/logs/geckodriver.log')

        self._driver = webdriver.Firefox(options=opts, service=serv)
        self._url = 'https://www.nytimes.com/games/wordle/index.html'
        self._localStorageScript = 'return JSON.parse(this.localStorage.getItem("nyt-wordle-state")).solution'
        self._last_updated = datetime.now().date()
        self._wotd = self._getWotd()

        # ensure that scraper is closed to avoid memory leaks
        register(self.close_scraper)

    def close_scraper(self) -> None:
        # WILL CAUSE MEMORY LEAK IF NOT CLOSED
        self._driver.quit()

    def _getWotd(self) -> str:
        """Webscrapes the official webpage to obtain the Word of the Day."""

        self._driver.get(self._url)
        return str(self._driver.execute_script(self._localStorageScript))

    def wotd(self, date: datetime) -> str:
        """Returns today's word."""

        # Potentially update today's word
        today = datetime.now().date()
        if self._last_updated < today:
            prev_wotd = self._wotd
            self._wotd = self._getWotd()
            self._last_updated = today

            # If we updated the word as user submit, return the previous word
            if date < today:
                return prev_wotd

        return self._wotd