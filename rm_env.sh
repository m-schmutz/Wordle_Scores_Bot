#!/bin/bash
red() {
    echo "\e[31m$1\e[0m"
}

blue() {
    echo "\e[34m$1\e[0m"
}

green() {
    echo "\e[92m$1\e[0m"
}

yellow() {
    echo "\e[33m$1\e[0m"
}

magenta() {
    echo "\e[35m$1\e[0m"
}

echo -e "==========================================================="
echo -e "Virtual Environment Removal"
echo -e "===========================================================\n"

if [ -d "env" ]; then
    env_path=$(cd ./env && pwd)
    echo -e "Virtual Environment found: ($env_path)"

else
    echo -e "Environment $(red "Environment not found")"
    exit 1
fi

read -p "Type 'yes' to confirm virtual environment removal: " remove

if [ "$remove" == "yes" ]; then   
    echo -e "$(yellow "Beginning virtual environment removal")"

    # rm -r ./env
    # equivalent to grep -v -e ‘^1’ -

    added_path=$(cd ./env/usr/bin && pwd)

    echo $added_path

    sed '/export PATH="$PATH:/home/msch/Projects/Wordle_Scores_Bot/env/usr/bin"/d' ~/.profile

    echo -e "$(green "Removal Completed")"
else 
    echo -e "\t$(red "REMOVAL ABORTED!!?!!!!!?")"
    sleep 1
    echo -e "\t\t$(magenta "bitch")"
    sleep 1
    echo -e "\t$(green "i bet u want ur console back huh?")"
    sleep 5
    echo -e "\t\t\t:-)"
    sleep 3
    echo -e "."
    sleep 1
    echo -e "."
    sleep 1
    echo -e "."
    sleep 1
    echo -e "."
    sleep 4
    echo -e "."
    sleep 15
    echo -e ">:-)"
    sleep 120
fi




# # ~/.profile: executed by the command interpreter for login shells.
# # This file is not read by bash(1), if ~/.bash_profile or ~/.bash_login
# # exists.
# # see /usr/share/doc/bash/examples/startup-files for examples.
# # the files are located in the bash-doc package.

# # the default umask is set in /etc/profile; for setting the umask
# # for ssh logins, install and configure the libpam-umask package.
# #umask 022

# # if running bash
# if [ -n "$BASH_VERSION" ]; then
#     # include .bashrc if it exists
#     if [ -f "$HOME/.bashrc" ]; then
# 	. "$HOME/.bashrc"
#     fi
# fi

# # set PATH so it includes user's private bin if it exists
# if [ -d "$HOME/bin" ] ; then
#     PATH="$HOME/bin:$PATH"
# fi

# # set PATH so it includes user's private bin if it exists
# if [ -d "$HOME/.local/bin" ] ; then
#     PATH="$HOME/.local/bin:$PATH"
# fi
# export PATH="$PATH:/home/msch/Projects/Wordle_Scores_Bot/env/usr/bin"
