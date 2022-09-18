from subprocess import run
from ansi import green
from os import getcwd, mkdir
from os.path import basename, exists

# objects to be imported
__all__ = ['install', 'remove']

# the name of the repository directory
REPO = 'Wordle_Scores_Bot'

# log files for setup
STDOUT_LOG = './lib/logs/setup.STDOUT'
STDERR_LOG = './lib/logs/setup.STDERR'

# path for directory to hold the bot logs
LOG_DIR = './lib/logs'

# path for directory to hold the bot database
DB_DIR = './lib/bot_database'
 
# executable to run shell commands with
BASH = '/bin/bash'

# command to update and upgrade packages
UPDATE_UPGRADE = 'sudo apt-get update -y && sudo apt-get upgrade -y'

# command to create virtual environment
CREATE_ENV = 'python3.10 -m venv ./venv'

# command to activate the virtual environment
ACTIVATE_ENV = 'source ./venv/bin/activate;'

# command to remove the virtual environment
REMOVE_ENV = 'rm -rf venv/'

# required apt packages
REQ_APT = [
    'firefox-geckodriver',
    'python3.10-venv',
    'tesseract-ocr' ]

# required pip packages
REQ_PIP = [
    '--upgrade pip',
    'opencv-python',
    'psutil',
    'pytesseract',
    'requests',
    'selenium',
    '--upgrade git+https://github.com/Rapptz/discord.py' ]


def install() -> None:
    # ensure that the present working directory is 'Wordle_Scores_bot'
    try: 
        assert(basename(getcwd()) == REPO)
    except:
        print(f'setup.py must be ran within the {REPO} directory')

    # create needed directories
    if not exists(LOG_DIR): mkdir(LOG_DIR)
    if not exists(DB_DIR): mkdir(DB_DIR)

    # notify user of progress
    print(green('lib subdirectories created'))

    # combine all apt commands needed
    apt_cmds = ';'.join(f'sudo apt-get install {pkg} -y' for pkg in REQ_APT) + ';sudo apt-get clean'

    # combine all pip commands needed
    pip_cmds = ACTIVATE_ENV+';'.join(f'pip3.10 install {pkg}' for pkg in REQ_PIP) + ';deactivate'


    with open(STDOUT_LOG, 'w') as outlog, open(STDERR_LOG, 'w') as errlog:

        # update and upgrade packages
        run(UPDATE_UPGRADE, stdin=0, stdout=outlog, stderr=errlog, shell=True, executable=BASH)

        # notify user of progress
        print(green('update/upgrade complete'))

        # install apt packages
        run(apt_cmds, stdout=outlog, stderr=errlog, shell=True, executable=BASH)

        # notify user of progress
        print(green('apt packages installed'))

        # create the virtual environment
        run(CREATE_ENV, stdout=outlog, stderr=errlog, shell=True, executable=BASH)

        # notify user of progress
        print(green('virtual environment created'))

        # install pip packages
        run(pip_cmds, stdout=outlog, stderr=errlog, shell=True, executable=BASH)

    # notify user that install is complete
    print(green('pip packages installed'))
    print(green('bot environment setup complete'))

def remove(all=False) -> None:
    with open(STDOUT_LOG, 'w') as outlog, open(STDERR_LOG, 'w') as errlog:
        # remove the virtual environment
        run(REMOVE_ENV, stdout=STDOUT_LOG, stderr=STDERR_LOG, shell=True, executable=BASH)

        # if user wants to remove all apt packages
        if all:
            # combine all apt commands to remove installed packages
            apt_cmds = ';'.join(f'sudo apt-get remove {pkg} -y' for pkg in REQ_APT[2:]) + ';sudo apt-get clean'

            # remove the installed commands
            run(apt_cmds, stdout=outlog, stderr=errlog, shell=True, executable=BASH)

            # notify user that remove-all completed
            print(green('virtual environment and apt packages removed'))
    
            return

        # notify user that remove completed
        print(green('virtual environment removed'))        