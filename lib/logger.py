from datetime import datetime
from types import TracebackType
from traceback import format_tb
from atexit import register

# defines the paths to the log files
BOT_LOG = './lib/logs/bot.log'
TB_LOG = './lib/logs/traceback.log'

# format the exception to be readable in log
def format_excs(dtime:datetime, user:str, exc_name:str, traceback:TracebackType) -> str:
    # get the print representation of the traceback
    tb = "".join(format_tb(traceback))
    # return the formatted entry
    return f'[{dtime.strftime("%m-%d-%Y %H:%M:%S")}] -> {user}, Exception: {exc_name}\n{tb}\n'
    

class LogUpdate():
    def __init__(self) -> None:
        # register log_shutdown method so that connection is closed on shutdown
        register(self._log_shutdown)


    # adds shutdown entry to the log file
    def _log_shutdown(self) -> None:
        # update log on bot shutdown
        self.update(datetime.now(), '', '', 'Shutdown')


    # adds start up entry to the log file
    def log_startup(self) -> None:
        # update log on bot startup
        self.update(datetime.now(), '', '', 'Start up')


    # append entry to file
    @staticmethod
    def update(dtime:datetime, server:str, user:str, event:str, traceback:TracebackType=None, exc_name:str='') -> None:
        # check if there is a traceback
        if traceback:
            # create traceback log entry if it exists
            tb_entry = format_excs(dtime, user, exc_name, traceback)

            # write the entry to the log file
            with open(TB_LOG, 'a') as log:
                log.write(tb_entry)

        # generate the log entry
        entry = f'{dtime.strftime("%m-%d-%Y %H:%M:%S")},{server},{user},{event},{exc_name}\n'

        # write the log entry to the log file
        with open(BOT_LOG, 'a') as log:
            log.write(entry)
    