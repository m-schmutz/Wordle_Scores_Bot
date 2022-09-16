#!/bin/python3.10
from sys import argv
from lib import *

def usage():
    print('Usage: python3.10 setup.py (install, remove or remove-all)')
    print('\t1. install: Creates new virtual environment with necessary packages')
    print('\t2. remove: Removes the virtual environment')
    print('\t3. remove-all: Removes the virtual environment and installed apt packages')
    quit()


# driver code
if __name__ == '__main__':

    # try to get the mode from the command line arguments
    try:
        mode = argv[1]
        assert(len(argv) == 2)
    # if there arent the correct amount of command line arguments, print proper usage
    except:
        usage()

    # swtich case to find the mode the user wants to use
    match mode:
        case 'install':
            install()
        case 'remove':
            remove()
        case 'remove-all':
            remove(all=True)
        case _:
            usage()