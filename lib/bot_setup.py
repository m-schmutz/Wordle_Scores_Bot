from os import pipe, fdopen, close
from subprocess import Popen, run, STDOUT, DEVNULL
from re import compile, sub, DOTALL

import lib.ansi as ansi
import lib.progressbar as pb

REQ_APT = [
    'firefox-geckodriver',
    'python3-venv',
    'tesseract-ocr' ]
REQ_PIP = [
    'discord',
    'opencv-python',
    'psutil',
    'pytesseract',
    'requests',
    'selenium' ]
BASH = '/bin/bash'
VENV = './venv'
INSTALLS_FILE = './lib/installs.txt'

def _venv_create() -> None:
    print('Creating virtual environment...', end=' ')
    run(f'python3 -m venv {VENV}', shell=True)
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
        run(cmds, shell=True, executable=BASH)

    return

def _install_apt_packages() -> None:    
    # Simulate install to get list of packages that will be installed.
    print('Obtaining list of APT packages...', end=' ')
    proc_sim  = run(f'sudo apt-get -s -y install {" ".join(REQ_APT)}', shell=True, capture_output=True)
    print(ansi.ansi('DONE').green())

    # Compile packages into:
    # 1. Formatted string - "pckg1 pckg2 ... pckgN", for installation command.
    # 2. List - [pckg1, pckg2, ..., pckgN], for package count and potential uninstall.
    regex_sim     = compile('The following NEW packages will be installed:\n(.*)\n\d', DOTALL)
    regex_result  = regex_sim.search(proc_sim.stdout.decode()).group(1)
    installs_str  = sub('\s+', ' ', regex_result).strip()
    installs_list = installs_str.split(' ')

    # Write list of packages to file for use when uninstalling.
    with open(INSTALLS_FILE, 'w') as f:
        print(*installs_list, sep='\n', file=f)

    # Initialize the progress bar.
    progbar = pb.ProgressBar(
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
    return

def _install_pip_packages() -> None:
    print('Installing PIP packages for virtual environment...', end=' ')
    _venv_run(f'pip3 install {" ".join(REQ_PIP)}', daemon=True)
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
    print('Removing virtual environment and all PIP packages...', end=' ')
    run([f'sudo rm -r {VENV}'], shell=True, stdout=DEVNULL, stderr=DEVNULL)
    print(ansi.ansi('DONE').green())

    # Read list of APT packages that were installed.
    with open(INSTALLS_FILE, 'r') as f:
        packages = [line.strip() for line in f.readlines()]

    # Initialize the progress bar.
    progbar = pb.ProgressBar(
        total=len(packages),
        titleoncomplete='APT Packages Removed.',
        left='|', right='|', fill_char='█', empty_char='░')
    progress = 0

    # Setup for parsing output of uninstall.
    regex_remove = compile('^Removing ([^ ]+) .*')
    rfd, wfd     = pipe()
    r            = fdopen(rfd, newline='')

    # Remove apt packages that were installed.
    proc = Popen([f'sudo apt-get -y purge {" ".join(packages)}'], shell=True, stdout=wfd, stderr=STDOUT)
    close(wfd)
    while proc.poll() == None:
        line = r.readline()

        match_remove = regex_remove.search(line)
        if match_remove:
            progress += 1
            progbar.update(progress, f'Removing {match_remove.group(1)}...')
            continue

    close(rfd)

    # Clear the cache as good practice.
    print('Cleaning up...', end=' ')
    run(['sudo apt-get clean'], shell=True, stdout=DEVNULL, stderr=DEVNULL)
    print(ansi.ansi('DONE').green())
    
    print('Wordle Bot successfully uninstalled.')
    return

def start() -> None:
    _venv_run('python3 ./lib/bot.py')
    return
