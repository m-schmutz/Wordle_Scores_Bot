from sqlite3 import connect
from os.path import exists
from datetime import datetime
from dataclasses import dataclass
from atexit import register
from typing import Tuple


LOG_DB_PATH = './lib/logs/log.db'

LOG_EVENTS = {1: 'submit', 2: 'new', 3: 'doublesub', 4: 'invalid', 5: 'rolldie', 6: 'link', 7: 'exception', 8: 'su/sd'}


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
        
        # register method so that connection is closed on shutdown
        register(self.close_connection)

        # check if database already exists
        existing = exists(LOG_DB_PATH)

        # connect to database, if it doesn't exist, a new one is created
        self._log = connect(LOG_DB_PATH)

        # only create tables if the database does not exist
        if not existing:
            with self._log as _cur:
                _cur.executescript('''
                CREATE TABLE BotLog (
                    event_time int,
                    user str, 
                    event str, 
                    msg str);

                CREATE TABLE Tracebacks (
                    event_time int,
                    tb str);
                ''')

    def close_connection(self) -> None:
        # close connection to database
        self._log.close()

    def update(self, dtime:datetime, user:str, event:str, msg:str, tb:str=None) -> None:
        
        # convert datetime to int
        event_time = dtime_to_dint(dtime)

        # 
        with self._log as _cur:
            _cur.execute(f'''
            INSERT INTO BotLog (
                event_time, 
                user, 
                event, 
                msg)
                Values (
                    {event_time},
                    '{user}', 
                    '{event}', 
                    '{msg}')''')

            if tb:
                _cur.execute(f'''
                INSERT INTO Tracebacks (
                    event_time, 
                    tb)
                    Values (
                        {event_time},
                        '{tb}')''')





class LogReader:
    def __init__(self) -> None:

        if not exists(LOG_DB_PATH):
            raise NoLogs

        register(self.close_connection)

        self._log = connect(LOG_DB_PATH)

    def close_connection(self) -> None:
        # close connection to database
        self._log.close()

    def logs_by_user(self, user:str) -> list:
        pass

    def logs_by_event(self) -> list:
        print('Events: ')
        print('1: Game submissions\n2: New User added\n3: Double Submissions\n4: Invalid Games\n5: Die Rolls\n6: Link Requests\n7: Exceptions\n8: Startup/Shutdowns')


    def logs_by_timeframe(self) -> list:
        pass