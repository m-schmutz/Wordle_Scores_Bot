from sqlite3 import connect
from os.path import exists
from datetime import datetime
from dataclasses import dataclass
from atexit import register
from typing import Tuple


LOG_DB_PATH = './lib/logs/log.db'

'''
log items: time, user, 
'''
#tb = f'[{current_time}]\n{"".join(format_tb(exc_tb))}\n\n'


def dtime_to_dint(dtime:datetime) -> int:
    return int(dtime.strftime('%Y%m%d%H%M%S'))

def dint_to_str(dint:int) -> str:
    dtime = datetime.strptime(str(dint), '%Y%m%d%H%M%S')
    return dtime.strftime('%m-%d-%Y %H:%M:%S')


class NoLogs(Exception):
    def __init__(self) -> None:
        self.msg = 'Log database does not exist'
        

class LogUpdate:
    def __init__(self) -> None:
        
        register(self.close_connection)

        existing = exists(LOG_DB_PATH)

        self._log = connect(LOG_DB_PATH)

        if not existing:
            with self._log as _cur:
                pass

    def close_connection(self) -> None:
        # close connection to database
        self._log.close()

    def update(self) -> None:
        pass


class LogReader:
    def __init__(self) -> None:

        if not exists(LOG_DB_PATH):
            raise NoLogs

        register(self.close_connection)

        self._log = connect(LOG_DB_PATH)

    def close_connection(self) -> None:
        # close connection to database
        self._log.close()