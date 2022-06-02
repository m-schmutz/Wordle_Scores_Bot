#!/bin/bash
###############################################################################################################################################################
###############################################################################################################################################################
### These are functions for turning the passed string to the color of the function name
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

###############################################################################################################################################################
###############################################################################################################################################################
### escape sequences to control cursor 
### for more info on ANSI codes: https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797

# saves cursor position
sc="\e[s"
# restores cursor to last save position
rc="\e[u"
# erases line from cursor position to the end of line
el="\e[0K"

###############################################################################################################################################################
###############################################################################################################################################################
### Check if the script is being sourced

# this is necessary for some actions to be successfully applied (example of this is when PATH variable is updated later on)
# for more info on using source: https://superuser.com/questions/46139/what-does-source-do
# essentially, it runs the script in the current shell rather than launching another process

# if the script is not being sourced, request user to run script again as source, then exit script
# stackoverflow once again to the rescue to figure out how to determine this: 
# https://stackoverflow.com/questions/2683279/how-to-detect-if-a-script-is-being-sourced
if [[ $0 == "$BASH_SOURCE" ]]; then
    echo -e "Please run script as source. This is required so that PATH is updated"
    echo -e "run as: source ./rm_env.sh"
    exit 1
fi

###############################################################################################################################################################
###############################################################################################################################################################
### Print out starting banner
echo -e "=================================================================================="
echo -e "\t\tVirtual Environment Removal"
echo -e "=================================================================================="

###############################################################################################################################################################
###############################################################################################################################################################
### Check that an environment exists
# check if 'env' directory exists
if [ -d "env" ]; then
    env_path=$(cd ./env && pwd)
    echo -e "Virtual Environment found: ($env_path)"

# else print error and exit script 
else
    echo -e "$(red "ERROR"): No environment found"
    return 1
fi
###############################################################################################################################################################
###############################################################################################################################################################
### Ensure that user wants to delete environment
read -p "Type 'yes' to confirm virtual environment removal: " remove

### if they do, delete env and remove environment path from PATH
if [ "$remove" == "yes" ]; then   
    echo -e "\n**********************************************************************************"
    echo -e "$(yellow "Beginning virtual environment removal")"

    echo -e "----------------------------------------------------------------------------------"
    echo -e "Removing virtual environment --> $sc$(yellow "working...")"
    # get the environment path before it is deleted
    env_path=$(cd ./env/usr/bin && pwd)
    # delete the virtual environment
    rm -r ./env
    echo -e "$rc$el$(green "done")"
    
    echo -e "----------------------------------------------------------------------------------"
    echo -e "Removing exported path in ~/.profile --> $sc$(yellow "working...")"

    fslash=\/
    bslash=\\\/

    ## https://reactgo.com/bash-replace-characters-string/
    # placing escape character before each forward slash so that it is read correctly by sed
    env_path="${env_path//[$fslash]/$bslash}"

    # construct line added to ~/.profile
    line="export PATH=\"\$PATH:$env_path\""

    # remove the line from ~/.profile
    sed -i "/$line/d" ~/.profile
    
    echo -e "$rc$el$(green "done")"

    echo -e "----------------------------------------------------------------------------------"

    echo -e "Removing environment path from PATH --> $sc$(yellow "working...")"

    # remove environment path from PATH
    PATH=${PATH//:$env_path/}

    echo -e "$rc$el$(green "done")"

    echo -e "----------------------------------------------------------------------------------"
else 
    echo -e "\t$(red "REMOVAL ABORTED!!?!!!!!?")"
    return 2
fi
echo -e "\n**********************************************************************************\n"

###############################################################################################################################################################
###############################################################################################################################################################
clear -x
echo -e "=================================================================================="
echo -e "\t\t$(green "Environment removal complete")"
echo -e "=================================================================================="