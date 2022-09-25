from datetime import datetime
from requests import get
from json import loads


def get_wotd(dtime:datetime) -> str:
    # convert datetime to string in form YYYY-MM-DD
    date = dtime.strftime('%Y-%m-%d')
    
    # send get request for JSON data
    r = loads(get(f'https://www.nytimes.com/svc/wordle/v2/{date}.json').text)
    
    # parse and return solution field
    return r['solution']


class WOTD:
    def __init__(self) -> None:
        # set last update to today
        self._last_updated = datetime.now().date()

        # get the word of the day
        self._wotd = get_wotd(self._last_updated)

    def wotd(self, date: datetime) -> str:
        """Returns today's word."""

        # Potentially update today's word
        today = datetime.now().date()
        if self._last_updated < today:
            prev_wotd = self._wotd
            self._wotd = get_wotd(today)
            self._last_updated = today

            # If we updated the word as user submit, return the previous word
            if date < today:
                return prev_wotd

        return self._wotd