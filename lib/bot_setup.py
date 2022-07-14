from os import pipe, fdopen, close
from subprocess import Popen, run, STDOUT, DEVNULL
from re import compile, sub, DOTALL

import lib.ansi as ansi
from lib.progressbar import ProgressBar


# _SUBP:
#   - If True, (u/i)nstallations will be handled behind the scenes. (NOT RECOMMENDED LOL)
#   - If False, (u/i)nstallations will be dumped to stdout.
_SUBP: bool = False
BASH = '/bin/bash'
VENV = './venv'
INSTALLS_FILE = './lib/installs.txt'
REQ_APT = [
    'firefox-geckodriver',
    'python3-venv',
    'tesseract-ocr' ]
REQ_PIP = [
    'opencv-python',
    'psutil',
    'pytesseract',
    'requests',
    'selenium' ]

def _venv_create() -> None:
    print('Creating virtual environment...', end=' ')
    run(f'python3 -m venv {VENV}', shell=True, stderr=STDOUT)
    print(ansi.ansi('DONE').green())
    return

def _venv_run(cmd, daemon=False) -> None:
    cmds = [f'\
        source {VENV}/bin/activate;\
        {cmd};\
        deactivate']

    if daemon:
        run(cmds, shell=True, executable=BASH, stdout=DEVNULL, stderr=DEVNULL)
    else:
        run(cmds, shell=True, executable=BASH, stderr=STDOUT)

    return

def _install_apt_packages() -> None:
    # Update apt
    print('Making sure apt is updated...')
    if _SUBP:
        run(f'sudo apt -y update', shell=True, stdout=DEVNULL, stderr=DEVNULL)
        run(f'sudo apt -y upgrade', shell=True, stdout=DEVNULL, stderr=DEVNULL)
    else:
        run(f'sudo apt -y update', shell=True, stderr=STDOUT)
        run(f'sudo apt -y upgrade', shell=True, stderr=STDOUT)
    print(ansi.ansi('APT Updated').green())

    # Simulate install to get list of packages that will be installed.
    print('Obtaining list of APT packages...', end=' ')
    stdout = run(f'sudo apt-get -s -y install {" ".join(REQ_APT)}', shell=True, capture_output=True).stdout

    # Compile packages into:
    # 1. Formatted string - "pckg1 pckg2 ... pckgN", for installation command.
    # 2. List - [pckg1, pckg2, ..., pckgN], for package count and potential uninstall.
    regex_sim     = compile('The following NEW packages will be installed:\n(.*)\n\d', DOTALL)
    regex_result  = regex_sim.search(stdout.decode()).group(1)
    installs_str  = sub('\s+', ' ', regex_result).strip()
    installs_list = installs_str.split(' ')
    print(ansi.ansi('DONE').green())

    if _SUBP:
        # Initialize the progress bar.
        progbar = ProgressBar(
            total=len(installs_list) * 3,
            titleoncomplete='APT Packages Installed.',
            left='|', right='|', fill_char='█', empty_char='░')
        progress = 0

        # Setup for parsing the output from installation
        regex_get    = compile('^Get:\d+ [^ ]+ [^ ]+ [^ ]+ ([^ ]+) .*')
        regex_unpack = compile('^Unpacking ([^ ]+) .*')
        regex_setup  = compile('^Setting up ([^ ]+) .*')
        rfd, wfd     = pipe()
        r            = fdopen(rfd, newline='')

        # Write list of packages to file for use when uninstalling.
        with open(INSTALLS_FILE, 'w') as f:
            print(*installs_list, sep='\n', file=f)

    # Install the packages!
        proc = Popen(f'sudo apt-get -y install {installs_str}', shell=True, stdout=wfd, stderr=STDOUT)
        close(wfd)
        while proc.poll() == None:
            line = r.readline()

            # Downloading...
            match_get = regex_get.search(line)
            if match_get:
                progress += 1
                progbar.update(progress, f'Downloading {match_get.group(1)}...')
                continue

            # Unpacking...
            match_unpack = regex_unpack.search(line)
            if match_unpack:
                progress += 1
                progbar.update(progress, f'Unpacking {match_unpack.group(1)}...')
                continue

            # Setting up...
            match_setup = regex_setup.search(line)
            if match_setup:
                progress += 1
                progbar.update(progress, f'Setting up {match_setup.group(1)}...')
                continue
        close(rfd)
    else:
        run(f'sudo apt-get -y install {installs_str}', shell=True, stderr=STDOUT)

    return

def _install_pip_packages() -> None:
    cmds = ';'.join([
        'pip3 install ' + ' '.join(REQ_PIP),
        'pip3 install --upgrade git+https://github.com/Rapptz/discord.py'])

    print('Installing PIP packages for virtual environment...', end=' ')
    if _SUBP:
        _venv_run(cmds, daemon=True)
    else:
        _venv_run(cmds)
    print(ansi.ansi('DONE').green())
    return

def install() -> None:
    _install_apt_packages()
    _venv_create()
    _install_pip_packages()

    print('Wordle Bot successfully installed.')
    return

def uninstall() -> None:
    # Remove virtual environment (this includes all pip packages).
    cmd = f'sudo rm -r {VENV}'
    print('Removing virtual environment and all PIP packages...', end=' ')
    if _SUBP:
        run(cmd, shell=True, stdout=DEVNULL, stderr=DEVNULL)
    else:
        run(cmd, shell=True, stderr=STDOUT)
    print(ansi.ansi('DONE').green())

    # Read list of APT packages that were installed.
    with open(INSTALLS_FILE, 'r') as f:
        packages = [line.strip() for line in f.readlines()]

    cmd = f'sudo apt-get -y purge {" ".join(packages)}'
    if _SUBP:
        # Initialize the progress bar.
        progbar = ProgressBar(
            total=len(packages),
            titleoncomplete='APT Packages Removed.',
            left='|', right='|', fill_char='█', empty_char='░')
        progress = 0

        # Setup for parsing output of uninstall.
        regex_remove = compile('^Removing ([^ ]+) .*')
        rfd, wfd     = pipe()
        r            = fdopen(rfd, newline='')

    # Remove apt packages that were installed.
        proc = Popen(cmd, shell=True, stdout=wfd, stderr=STDOUT)
        close(wfd)
        while proc.poll() == None:
            line = r.readline()

            match_remove = regex_remove.search(line)
            if match_remove:
                progress += 1
                progbar.update(progress, f'Removing {match_remove.group(1)}...')
                continue
        close(rfd)
    else:
        run(cmd, shell=True, stderr=STDOUT)

    # Clear the cache as good practice.
    print('Cleaning up...', end=' ')
    if _SUBP:
        run('sudo apt-get clean', shell=True, stdout=DEVNULL, stderr=DEVNULL)
    else:
        run('sudo apt-get clean', shell=True, stderr=STDOUT)
    print(ansi.ansi('DONE').green())
    
    print('Wordle Bot successfully uninstalled.')
    return

def start() -> None:
    _venv_run('python3 ./lib/bot.py')
    return
