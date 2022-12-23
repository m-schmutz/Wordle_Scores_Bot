from datetime import datetime
from types import TracebackType
from traceback import format_tb
from atexit import register

# defines the paths to the log files
BOT_LOG = './lib/logs/bot.log'
TB_LOG = './lib/logs/traceback.log'


class BotLog():
    '''
    This is the logger for the WordleBot
    
    ---
    All logs for the bot are stored in the lib/logs directory
    - bot.log: logs all bot/user interactions
    - traceback.log: contains the tracebacks of any exceptions that have occurred
    '''
    def __init__(self) -> None:
        # register when bot terminates so that log is updated
        # (This makes sure that the log will be updated on an unexpected shutdown)
        register(self._log_shutdown)


    # adds shutdown entry to the log file
    def _log_shutdown(self) -> None:
        # update log on bot shutdown
        self.update(datetime.now(), 'Shutdown')


    # adds start up entry to the log file
    def log_startup(self) -> None:
        # check that the log has proper header
        with open(BOT_LOG, 'r+') as log:
            # check if the log is empty
            if not len(log.readline()):
                # write header if no logs are present
                log.write('datetime,event,exc_name,server,user,win,guesses,greens,yellows,uniques\n')
        
        # update log on bot startup
        self.update(datetime.now(), 'Startup')


    # format the exception to be readable in log
    @staticmethod
    def format_excs(dtime:datetime, user:str, exc_name:str, traceback:TracebackType) -> str:
        # get the print representation of the traceback
        tb = "".join(format_tb(traceback))

        # return the formatted entry
        return f'[{dtime.strftime("%m-%d-%Y %H:%M:%S")}] -> {user}, Exception: {exc_name}\n{tb}\n'


    # append entry to file
    def update(self, dtime:datetime, event:str, exc_name:str='', server:str='', user:str='', win:str='', guesses:str='', greens:str='', yellows:str='', uniques:str='', traceback:TracebackType=None) -> None:
        # check if there is a traceback
        if traceback:
            # create traceback log entry if it exists
            tb_entry = self.format_excs(dtime, user, exc_name, traceback)

            # write the entry to the log file
            with open(TB_LOG, 'a') as log:
                log.write(tb_entry)

        # generate the log entry
        entry = f'{dtime.strftime("%m-%d-%Y %H:%M:%S")},{event},{exc_name},{server},{user},{win},{guesses},{greens},{yellows},{uniques}\n'

        # write the log entry to the log file
        with open(BOT_LOG, 'a') as log:
            log.write(entry)
    