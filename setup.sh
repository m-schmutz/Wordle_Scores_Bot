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
    echo -e "run as: source ./setup.sh"
    exit 1
fi

###############################################################################################################################################################
###############################################################################################################################################################
### Print out starting banner
echo -e "=================================================================================="
echo -e "\t\tBeginning Virtual Environment Setup"
echo -e "=================================================================================="

###############################################################################################################################################################
###############################################################################################################################################################
### Check that this script is being run from the git repository

# check if current directory is the Wordle_Scores_Bot directory
# if not in the correct directory, exit the script
# Note: 'return' is used in place of 'exit' in this case because at this point we know
# the script is being sourced (check at line 47 ensures this)
# if exit was used, the shell would be closed, return simply stops the script
if [ $(basename $PWD) != "Wordle_Scores_Bot" ]; then
    echo -e "$(red "ERROR"): Script must be run within Wordle_Scores_Bot directory"
    return 1
fi

###############################################################################################################################################################
###############################################################################################################################################################
### Check that apt is up to date.

# if apt is out-of-date, then some required packages will not be found when requested from apt
echo -e "\n**********************************************************************************"

# inform user that latest version of apt is needed
echo -e "Checking that apt is up to date (This is necessary to get latest packages)"
echo -e "Running apt update --> $sc$(yellow "working...")"

# run apt update, direct output to /dev/null to avoid command line clutter
sudo apt update -y > /dev/null 2> /dev/null 
echo -e "$el"
echo -e "$rc$el$(green "done")"

# inform user that apt is being upgraded
echo -e "Running apt upgrade --> $sc$(yellow "working...")"

# run apt upgrade, again direct output to /dev/null
sudo apt upgrade -y > /dev/null 2> /dev/null
echo -e "$rc$el$(green "done")"

###############################################################################################################################################################
###############################################################################################################################################################
### Check if env directory exists

echo -e "\n**********************************************************************************"

# check if ./env directory exists
if [ -d "env" ]; then
    echo -e "Looking for virtual environment --> $(green "Found")"

# if ./env directory is not found, create a new one
else
    echo -e "Looking for virtual environment --> $(red "Not Found")"
    echo -e "\tInstalling virtual environment --> $sc$(yellow "Installing...")"
    
    # install the python3-venv package and create the virtual environment
    sudo apt install python3-venv > /dev/null 2> /dev/null
    python3 -m venv ./env > /dev/null

    # check that environment was successfully created
    if [ -d "env" ]; then 
        echo -e "$rc$el$(green "Installed")"

        echo -e "----------------------------------------------------------------------------------"
        # create the /env/usr/bin directory so that path can be added to PATH
        echo -e "Creating ./env/usr/bin directory --> $sc$(yellow "working...")"
        mkdir ./env/usr && mkdir ./env/usr/bin
        echo -e "$rc$el$(green "done")"

    # else print that process failed and exit script
    else
        echo -e "$rc$el$(red "Failed")"
        echo -e "\t$(red "Exiting"): Setup cannot continue without environment being created"
        return 1
    fi
fi


###############################################################################################################################################################
###############################################################################################################################################################
### Check the .profile file to see if path export is present. If it is not, add it.

echo -e "\n**********************************************************************************"

# get the path to the env/usr/bin
env_path=($(cd ./env/usr/bin && pwd))

# check if the exported path is in the .profile file
if [ $(grep -c "\$PATH:$env_path" ~/.profile) != 0 ]; then
    echo -e "environment path export --> $(green "Found")"

# if the path export is not in the .profile file, add it
else
    echo -e "environment path export --> $sc$(red "Not found")"
    sleep 0.5
    echo -e "$rc$sc$el$(yellow "Adding export")"
    echo -e "export PATH=\"\$PATH:$env_path\"" >> ~/.profile

    # update the users path by running the .profile file
    source ~/.profile
    echo -e "$rc$el$(green "Export added")"
fi

#clear the screen
clear -x
###############################################################################################################################################################
###############################################################################################################################################################
### Install required pip packages into the python environment
echo -e "\n**********************************************************************************"
echo -e "Reading pip_packages.txt"

# comment character in txt file, null allows us to ignore blank lines
comment="#"
null=""

# check that the pip_packages.txt file exists
if [ -f "./env_setup/pkg_lists/pip_packages.txt" ]; then

    # create array for holding names of pip packages
    declare -a pip_pkgs=()

    # read all lines in the pip_packages.txt file
    while read -r line; do

        # check if the first character is a comment character or a blank line
        if [[ "${line::1}" == $comment || $line == $null ]]; then

            # move to next line
            continue
        else
            # add the line to the packages array
            pip_pkgs+=("$line")
        fi
    # weird bash syntax
    done < ./env_setup/pkg_lists/pip_packages.txt

    # activate the python environment
    # this is so that packages are installed into the python environment
    source ./env/bin/activate
    
    # loop through all packages in the arrray
    for pkg in "${pip_pkgs[@]}" 
    do 
        echo -e "----------------------------------------------------------------------------------"
        # check if the package is already installed
        if [ $(pip3 list | grep -c "$pkg") != 0 ]; then
            echo -e "$pkg --> $(green "Found")"
        
        # if package is not found, install it
        else
            echo -e "$pkg --> $(red "Not found")"
            echo -e "\tInstalling $pkg --> $sc$(yellow "Installing...")"
            
            # install the python package using pip3
            pip3 install $pkg > /dev/null 2> /dev/null
            
            # check that the package was installed
            if [ $(pip3 list | grep -c "$pkg") != 0 ]; then
                echo -e "$rc$el$(green "Installed")"
            else
                echo -e "$rc$el$(red "Failed")"
            fi
        fi
        echo -e "----------------------------------------------------------------------------------"
    done

    # deactivate the python virtual environment
    # no longer necessary
    deactivate

else
    # skip above step if the pip_packages.txt file cannot be found
    echo -e "$(red "ERROR"): pip_packages.txt could not be found in ./env_setup/pkg_lists/"
fi

# clear the screen
clear -x 

###############################################################################################################################################################
###############################################################################################################################################################
### Install required debian packages into the environment

echo -e "\n**********************************************************************************"
echo -e "Reading deb_packages.txt"

# create array for holding names of deb packages
declare -a deb_pkgs=()

# read each line of the deb_packages.txt file 
while read -r line; do
    # check if line is a comment or blank line
    if [[ "${line::1}" == $comment || $line == $null ]]; then
        continue
    else
        # store line into the deb_pkgs array
        deb_pkgs+=("$line")
    fi
done < ./env_setup/pkg_lists/deb_packages.txt

# remove any deb packages in the directory
# to prevent installing the wrong package
rm *.deb 2>/dev/null

# loop through each item in the names list and check if it is present
for pkg in "${deb_pkgs[@]}"
do 
    echo -e "----------------------------------------------------------------------------------"
    # get the info from the package
    info=$(apt show $pkg 2> /dev/null | grep "Source: " | sed 's/Source: //g')
    
    # check if package has a Source: field
    if [[ $info != $null ]]; then
        # set $cmd to the source field
        cmd=$info
    else
        # otherwise cmd is $pkg
        cmd=$pkg
    fi

    # get the pkg_path so that we can test if it is present
    pkg_path="$(cd ./env/usr/bin && pwd)/$cmd"

    # check if the deb package is installed
    if command -v $cmd > /dev/null && [ $(command -v $cmd) == $pkg_path ]; then
        echo -e "$cmd --> $(green "Present")"

    # otherwise install the deb package to the usr/bin directory
    else
        echo -e "$pkg --> $sc$(red "Not found")"
        sleep 0.5
        echo -e "$rc$sc$el$(yellow "Installing")"
        
        # download the deb package using apt
        apt download $pkg > /dev/null 2>/dev/null
        
        # get the name of the deb package
        deb_package=$(find ./ -regex ".*.deb")

        # extract the files from the deb package into the /env/usr directory
        # dpkg-deb -x (extract) will automatically put the files into the usr/ directory
        dpkg-deb -x $deb_package ./env

        # rm the deb package
        rm *.deb

        # check that the package was installed to the correct directory (/env/bin)
        if command -v $cmd && [ $(command -v $cmd) == $pkg_path ]; then
            echo -e "$rc$el$(green "Installed")"
        else
            echo -e "$rc$el$(red "Failed")"
        fi
    fi
    echo -e "----------------------------------------------------------------------------------"
done
echo -e "\n**********************************************************************************"

clear -x
echo -e "=================================================================================="
echo -e "\t\t$(green "Environment setup complete")"
echo -e "=================================================================================="
###############################################################################################################################################################
###############################################################################################################################################################