import requests
import pickle
from datetime import datetime, time

# CONSTANTS ################################################################################
############################################################################################
_DEBUG_PRINT    = False

DATA_PATH       = './data.p'
EPOCH_START     = int(datetime(2021, 6, 19, 0, 0, 0, 0).timestamp())
SEC_PER_DAY     = int(60 * 60 * 24)
HTML_URL        = 'https://www.nytimes.com/games/wordle/index.html'
HTML_STRBEG     = 'src=\"main.'
HTML_STREND     = '.js'
JS_URL          = 'https://www.nytimes.com/games/wordle/main.{0}.js'
JS_STRBEG       = 'ko='
JS_STREND       = ']'

# INTERNAL FUNCTIONS #######################################################################
############################################################################################

# _epoch_today: ____________________________________________________________________________
# Round the current EPOCH time down to nearest day (12:00 a.m.)
def _epoch_today():
    return int(datetime.combine(datetime.now(), time.min).timestamp())

# _substr_request: _________________________________________________________________________
# Find the first occurence of a substring, that begins with *prefix* and ends
# with *suffix*, within the *.text* field of the response.
def _substr_request(url, prefix, sufffix):
    # Request the provided url
    res = requests.get(url)

    # Search for substring
    raw = res.text
    beg = raw.find(prefix) + len(prefix)
    end = raw.find(sufffix, beg)
    assert(beg >= 0 and end >= 0)

    # Return the substring
    return raw[beg:end]

# _update_wotd: ____________________________________________________________________________
# Using the requests module, we retrieve and parse the relavant data from
# Wordle's website. The data is then saved to file. This should only be
# called by *wotd()* when a new day is detected.
def _update_wotd():
    # Request the necessary data from their website.
    #   1.  The main Wordle webpage to obtain the JavaScript sourcefile name.
    #   2.  The Javascript file which contains the list of known words, ko.
    hash = _substr_request(HTML_URL, HTML_STRBEG, HTML_STREND)
    assert(hash)
    ko_raw = _substr_request(JS_URL.format(hash), JS_STRBEG, JS_STREND)
    assert(ko_raw)
    ko = ko_raw.strip('][').replace('\"', '').split(',')

    # Here we mimic Wordle's "Word of the Day" (WOTD) function and
    # use the same input data. The start date Wordle uses is:
    #   GMT: Saturday, June 19, 2021 12:00:00 AM
    epoch   = _epoch_today()
    index   = (epoch - EPOCH_START) // SEC_PER_DAY
    wotd    = ko[index]
    if _DEBUG_PRINT:
        print(f'Today\'s epoch: {epoch}')
        print(f'ko[{index}]: {wotd}')

    # Save info to file and return the WOTD
    data = { 'day': epoch, 'wotd': wotd }
    outfile = open(DATA_PATH, 'wb')
    pickle.dump(data, outfile)
    outfile.close()
    if _DEBUG_PRINT: print('WOTD updated!')

    return wotd



# USER FUNCTIONS ###########################################################################
############################################################################################

# wotd: ____________________________________________________________________________________
# Returns the WOTD. This compares the current day's epoch with that of the file
# so that the WOTD can be updated when needed.
def wotd():
    # Load WOTD data from file
    try: infile = open(DATA_PATH, 'rb')
    except FileNotFoundError:
        return _update_wotd()

    data = pickle.load(infile)
    infile.close()

    # Update data if it's old
    if _epoch_today() > data['day']:
        return _update_wotd()

    return data['wotd']

print(wotd())