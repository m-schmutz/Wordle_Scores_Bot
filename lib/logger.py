from os.path import exists
from datetime import datetime
from atexit import register
from traceback import format_tb
from types import TracebackType
from sys import exit

###############################################################################################
# store each log entry as a single line in log file
# log entries: server, user, event, message, traceback (if applicable)
# maybe keep track of what line in the file we are on to skip to it when generating log reader
###############################################################################################



class LogUpdate():
    def __init__(self) -> None:

        # register method so that connection is closed on shutdown
        register(self.log_shutdown)

    def log_shutdown(self) -> None:
        self.update()


    # append entry to file
    def update(self) -> None:
        pass