from datetime import datetime
from types import TracebackType
from traceback import format_tb
from atexit import register

# defines the paths to the log files
BOT_LOG = './lib/logs/bot.log'
TB_LOG = './lib/logs/traceback.log'


class BotLog():
    '''
    This is a logger for the WordleBot
    
    ---
    All logs for the bot are stored in the lib/logs directory
    - bot.log: logs all bot/user interactions
    - traceback.log: contains the tracebacks of any exceptions that have occurred
    '''
    def __init__(self) -> None:
        # register when bot terminates so that log is updated
        # (This makes sure that the log will be updated on an unexpected shutdown)
        register(self._log_shutdown())


    # adds shutdown entry to the log file
    def _log_shutdown(self) -> None:
        # update log on bot shutdown
        self.update(datetime.now(), '', '', 'Shutdown')


    # adds start up entry to the log file
    def log_startup(self) -> None:
        # update log on bot startup
        self.update(datetime.now(), '', '', 'Start up')


    # format the exception to be readable in log
    @staticmethod
    def format_excs(dtime:datetime, user:str, exc_name:str, traceback:TracebackType) -> str:
        # get the print representation of the traceback
        tb = "".join(format_tb(traceback))

        # return the formatted entry
        return f'[{dtime.strftime("%m-%d-%Y %H:%M:%S")}] -> {user}, Exception: {exc_name}\n{tb}\n'


    # append entry to file
    def update(self, dtime:datetime, server:str, user:str, event:str, traceback:TracebackType=None, exc_name:str='', guesses:str='') -> None:
        # check if there is a traceback
        if traceback:
            # create traceback log entry if it exists
            tb_entry = self.format_excs(dtime, user, exc_name, traceback)

            # write the entry to the log file
            with open(TB_LOG, 'a') as log:
                log.write(tb_entry)

        # generate the log entry
        entry = f'{dtime.strftime("%m-%d-%Y %H:%M:%S")},{server},{user},{event},{exc_name}\n'

        # write the log entry to the log file
        with open(BOT_LOG, 'a') as log:
            log.write(entry)
    