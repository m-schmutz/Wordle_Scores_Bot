from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from datetime import datetime

class WordleRequests:
    """Keeps track of the Word of the Day. Uses Selenium to webscrape the NYTimes Wordle webpage to retrieve it.
    
    ---
    ## Methods
    
    wotd() -> str
        Returns the Word of the Day."""

    def __init__(self) -> None:
        options = webdriver.FirefoxOptions()
        options.headless = True
        options.page_load_strategy = 'eager'
        service = Service(log_path='./lib/geckodriver.log')

        self._driver = webdriver.Firefox(options=options, service=service)
        self._last_updated = datetime.now().date()
        self._wotd = self._scrape()

    def __del__(self) -> None:
        # WILL CAUSE MEMORY LEAK IF NOT CLOSED
        self._driver.quit()

    def _scrape(self) -> str:
        """Webscrapes the official webpage to obtain the Word of the Day."""

        self._driver.get('https://www.nytimes.com/games/wordle/index.html')
        return str(self._driver.execute_script('return JSON.parse(this.localStorage.getItem("nyt-wordle-state")).solution'))

    def wotd(self) -> str:
        """Returns today's word."""

        now = datetime.now().date()
        if self._last_updated < now:
            self._last_updated = now
            self._wotd = self._scrape()

        return self._wotd
