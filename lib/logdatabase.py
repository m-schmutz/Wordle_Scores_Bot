from sqlite3 import connect
from os.path import exists
from datetime import datetime
from atexit import register
from traceback import format_tb
from types import TracebackType
from sys import exit

# log path
LOG_DB_PATH = './lib/logs/log.db'

# log events
LOG_EVENTS = {1: 'submit', 2: 'new', 3: 'doublesub', 4: 'invalid', 5: 'rolldie', 6: 'link', 7: 'exception', 8: 'su/sd'}

# convert datetime object into an int
def dtime_to_dint(dtime:datetime) -> int:
    return int(dtime.strftime('%Y%m%d%H%M%S'))

# convert date int to string
def dint_to_str(dint:int) -> str:
    dtime = datetime.strptime(str(dint), '%Y%m%d%H%M%S')
    return dtime.strftime('%m-%d-%Y %H:%M:%S')

# format a log entry into a string
def format_entry(entry) -> str:
    time, user, event, msg = entry
    return f'[{dint_to_str(time)}] -> {user}, {event}: {msg}\n'

# format exception log entries with respective tracebacks
def format_excs(entry) -> str:
    time, user, event, msg, time, tb = entry
    return f'[{dint_to_str(time)}] -> {user}, {event}: {msg}\n{tb}\n'

# function to save output to file or print to string
def manage_output(entries:list) -> None:
    # print prompt
    print('Enter file name to store log entries')
    print('Leave blank to print entries to screen')
    file = str(input('> '))

    # check if user entered a name
    if len(file) != 0:
        with open(file, 'w') as f:
            f.writelines(entries)

    # otherwise print the output to screen
    else:
        for entry in entries:
            print(entry)
        print()
        input('Press Enter to continue...')
    return

# exception raised if there is no log present
class NoLogs(Exception):
    def __init__(self) -> None:
        self.msg = 'Log database does not exist'
        
# class to update the log
class LogUpdate:
    def __init__(self) -> None:
        
        # register method so that connection is closed on shutdown
        register(self.log_shutdown)

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

    def log_shutdown(self) -> None:
        # update log on bot shutdown
        self.update(datetime.now(), 'WordleBot', 'su/sd', 'WordleBot Shutting down')
        
        # close connection to database
        self._log.close()


    def update(self, dtime:datetime, user:str, event:str, msg:str, traceback:TracebackType=None) -> None:
        # format the traceback information as a string
        tb = "".join(format_tb(traceback))

        # convert datetime to int
        event_time = dtime_to_dint(dtime)

        # insert new entry into the BotLog table
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

            # if a traceback is given then log the traceback as well
            if tb:
                _cur.execute(f'''
                INSERT INTO Tracebacks (
                    event_time, 
                    tb)
                    Values (
                        {event_time},
                        '{tb}')''')

# class to read the log
class LogReader:
    def __init__(self) -> None:
        # check that a log exists
        if not exists(LOG_DB_PATH):
            raise NoLogs

        # ensure that the database connection is closed on exit
        register(self._close_connection)

        # connect to the log database
        self._log = connect(LOG_DB_PATH)

    # Provides interface for looking up and storing logs
    def interface(self) -> None:
        # this is used to catch keyboard interupts to end program
        try:
            # while the user is still using the program
            while True:
                # while the user has not given valid input
                while True:
                    # prompt
                    print('Select Search Type: ')
                    print('1: By User\n2: By Event\n3: By Timeframe\n4: Exception/Tracebacks\n5: All Logs')
                    # get user input
                    try: 
                        stype = input('> ')
                        # check that input is valid
                        stype = int(stype)
                        assert(stype >= 1 and stype <= 5)
                        # break out of loop if no exceptions are raised
                        break
                    except (ValueError, AssertionError):
                        # clear screen and print error message
                        print('\033[2J\033[H',end='')
                        print(f'Invalid input: {stype}')
                
                # send user to correct search
                match stype:
                    case 1:
                        self.logs_by_user()
                    case 2: 
                        self.logs_by_event()
                    case 3:
                        self.logs_by_timeframe()
                    case 4:
                        self.exception_logs()
                    case 5:
                        self._all_logs()
                
                # clear screen 
                print('\033[2J\033[H',end='')

        # if keyboard interupt is given, end program
        except KeyboardInterrupt:
            print()
            exit()

    # gets all log entries
    def all_logs(self) -> None:
        # get all logs entries
        logs = self._all_logs()
        # manage output
        manage_output(logs)

    # read logs by user
    def logs_by_user(self) -> None:
        # get all the users in the database
        users = self._get_unique_users()
        registry = {i+1: user for i, user in users}

        # loop until user uses CTRL-C
        try:
            while True:
                # loop until user gives valid input
                while True:
                    print('Pick a user: ')
                    for i, user in registry.items():
                        print(f'{i}: {user}')
                    try:
                        user_ind = input('> ')
                        user_ind = int(user_ind)
                        user = registry[user_ind]
                        break
                    except (ValueError, KeyError):
                        print('\033[2J\033[H',end='')
                        print(f'Invalid input: {user_ind}')
                
                entries = self._get_by_user(user)
                manage_output(entries)
                # clear screen 
                print('\033[2J\033[H',end='')
        
        # exit when CTRL-C is received
        except KeyboardInterrupt:
            return


    def logs_by_event(self) -> None:
        # loop until we receive CTRL-C
        try: 
            while True:
                # loop until we get valid input
                while True:
                    print('Pick an event to view: ')
                    print('1: Game submissions\n2: New User added\n3: Double Submissions\n4: Invalid Games\n5: Die Rolls\n6: Link Requests\n7: Exceptions\n8: Startup/Shutdowns')
                    # get user input, break if it is valid
                    try:
                        event_ind = input('> ')
                        event_ind = int(event_ind)
                        event = LOG_EVENTS[event_ind]
                        break
                    except (ValueError, KeyError):
                        print('\033[2J\033[H',end='')
                        print(f'Invalid input: {event_ind}')
                
                # get entries of event
                entries = self._get_by_event(event)
                # send output to be printed or saved to file
                manage_output(entries)
                
                # clear screen 
                print('\033[2J\033[H',end='')

        # exit when CTRL-C is received   
        except KeyboardInterrupt:
            return


    def logs_by_timeframe(self) -> None:
        print('NOT IMPLEMENTED YET')


    def exception_logs(self, last:int = None) -> None:
        # get all exceptions
        excs = self._get_exc_info()

        # loop until we have valid user input
        while True:
            print('Enter the amount of latest tracebacks you want')
            print('Leave blank to get all tracebacks')
            # get user input, break if input is valid
            try:
                last = input('> ')
                if len(str(last)) == 0:
                    break
                last = int(last)
                assert(last <= len(excs))
                break
            except (ValueError, AssertionError):
                print('\033[2J\033[H',end='')
                print(f'Invalid input: {last}')
        
        # slice list of exceptions if requested by user
        if last:
            excs = excs[-last:]

        # send output to be printed or saved to file
        manage_output(excs)
        return


        
    def _close_connection(self) -> None:
        # close connection to database
        self._log.close()


    def _all_logs(self) -> list:
        # get all entries from the database
        with self._log as _cur:
            entries = _cur.execute('SELECT * FROM BotLog').fetchall()
        
        # return list of each entry as a string
        return list(map(format_entry, entries))


    def _get_by_event(self, event:str) -> list:
        # get all entries that are of the passed event 
        with self._log as _cur:
            entries = _cur.execute(f"SELECT * FROM BotLog WHERE event = '{event}'").fetchall()
        # return as a list of strings
        return list(map(format_entry, entries))


    def _get_exc_info(self) -> list:
        # get all entries which are exceptions and also grab their respective tracebacks
        with self._log as _cur:
            excs_tbs = _cur.execute("SELECT * FROM BotLog LEFT JOIN Tracebacks ON BotLog.event_time = Tracebacks.event_time WHERE event = 'exception'").fetchall()

        # return as a list of strings
        return list(map(format_excs, excs_tbs))


    def _get_by_user(self, user:str) -> list:
        # get all entries that are of the passed user
        with self._log as _cur:
            entries = _cur.execute(f"SELECT * FROM BotLog WHERE user = '{user}'").fetchall()
        # return as a list of strings
        return list(map(format_entry, entries))


    def _get_unique_users(self) -> list:
        # get all unique users from the BotLog table
        with self._log as _cur:
            users = _cur.execute('SELECT DISTINCT user from BotLog').fetchall()
        # return as a list of each username
        return [(i, user[0]) for i, user in enumerate(users)]