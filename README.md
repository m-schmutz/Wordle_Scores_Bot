# Discord Wordle Bot

## Python 3.10
### To run the bot, python3.10 needs to be installed. The steps for installation are listed below:

Install Python3.10 on Ubuntu https://computingforgeeks.com/how-to-install-python-on-ubuntu-linux-system/
1. sudo apt update && sudo apt upgrade
2. sudo apt install software-properties-common
3. sudo add-apt-repository ppa:deadsnakes/ppa
4. sudo apt install python3.10

# Bot Setup
### To setup the bot's environment follow the steps below

1. Clone this repository
2. Within repository, run `python3.10 setup.py install` or `chmod +x setup.py` and then simply `./setup.py install`.

# Running the Bot
### After the bot's environment is setup the bot can be run two ways:
1. run `source ./venv/bin/activate` and then `python3.10 run_bot.py`
2. run `chmod +x run_bot.py` and then `./run_bot.py`

# Uninstall
### When uninstalling the bot, there are two options:
1. run `python3.10 setup.py remove` to remove the virtual environment
2. run `python3.10 setup.py remove-all` to remove the virtual environment and the installed apt packages