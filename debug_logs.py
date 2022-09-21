#!./venv/bin/python3.10
from re import findall, search

BOT_LOG = './lib/logs/bot.log'
TB_LOG = './lib/logs/tracebacks.log'

LOG_RE = '\[[0-9\-: ]*\] Exception .*'
TB_RE = '(\[[0-9\-: ]*\]\n([\S ]+\n)+)'
TIME_RE = '[0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}'

class LogReader:
    def __init__(self) -> None:
        self.entries = self.match_excs()
  
    @staticmethod
    def parse_bot_log() -> list[str]:
        with open(BOT_LOG, 'r') as log:
            log_excs = findall(LOG_RE, log.read())
        return log_excs

    @staticmethod
    def parse_tb_log() -> list[str]:
        with open(TB_LOG, 'r') as log:
            tbs = findall(TB_RE, log.read())
        return tbs

    def match_excs(self) -> dict[str, str]:
        logs = self.parse_bot_log()
        tbs = self.parse_tb_log()

        entries = dict()

        for log, tb in zip(logs, tbs):

            log_time = search(TIME_RE, log).group()
            tbs_time = search(TIME_RE, tb[0]).group()
            assert(log_time == tbs_time)

            entries[log_time] = (log[22:], tb[0][22:])

        return entries


    def list_exc_entries(self) -> None:
        for time, logs in self.entries.items():
            print(f'{time}: {logs[0]}')
            print(logs[1])


def main():
    logs = LogDebug()

    logs.list_entries()
    




if __name__ == '__main__':
    main()