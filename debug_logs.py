#!./venv/bin/python3.10
from re import findall, search

BOT_LOG = './lib/logs/bot.log'
TB_LOG = './lib/logs/tracebacks.log'

LOG_RE = '\[[0-9\-: ]*\] Exception .*'
TB_RE = '(\[[0-9\-: ]*\]\n([\S ]+\n)+)'
TIME_RE = '[0-9]{2}-[0-9]{2}-[0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}'

class LogDebug:
    def __init__(self) -> None:
        self.entries = None 
       


def parse_bot_log() -> list[str]:
    with open(BOT_LOG, 'r') as log:
        log_excs = findall(LOG_RE, log)
    return log_excs

def parse_tb_log() -> list[str]:
    with open(TB_LOG, 'a') as log:
        tbs = findall(TB_RE, log)
    return tbs

def match_entries():
    logs = parse_bot_log()
    tbs = parse_tb_log()

    for log, tb in zip(logs, tbs):
        log_time = search(TIME_RE, log).group()
        tbs_time = search(TIME_RE, tb).group()
        assert(log_time == tbs_time)


def main():
    print(search(TIME_RE, '[09-20-2022 15:12:24] Bot Starting up').group())
    




if __name__ == '__main__':
    main()