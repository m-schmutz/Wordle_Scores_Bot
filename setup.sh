#!/bin/bash
# print out starting banner 
echo -e "==========================================================="
echo -e "Beginning Virtual Environment Setup"
echo -e "===========================================================\n"

# check that apt is up to date, issues arise when apt is out of date.
echo -e "Checking that apt is up to date (This can take a while if apt is out of date): \033[s"
sudo apt -y update -y > /dev/null 2> /dev/null && sudo apt upgrade -y > /dev/null 2> /dev/null
echo -e "\033[u\033[92mdone\033[0m"
#check that this script is being run from the git repository
if [ $(basename $PWD) != "Wordle_Scores_Bot" ]; then
    echo -e "setup needs to be ran in Wordle_Scores_Bot directory"
    exit 1
fi

echo -e "***********************************************************"
# check if env directory exists
if [ -d "env" ]; then
    echo -e "Looking for virtual environment --> \033[92mPresent\033[0m"
    # else create virtual environment
else
    echo -e "Looking for virtual environment --> \033[s\033[31mNot Present\033[0m"
    sleep 0.5
    echo -e "\033[u\033[s\033[0K\033[33mInstalling\033[0m"
    # install the python3-venv extension and create the virtual environment
    sudo apt install python3-venv > /dev/null 2> /dev/null
    python3 -m venv ./env > /dev/null
    # check that environment was successfully created
    if [ -d "env" ]; then 
        echo -e "\033[u\033[0K \033[92mInstalled\033[0m"
    # else print that process failed
    else
        echo -e "\033[u\033[0K \033[31mFailed\033[0m"
        echo -e "Exiting, cannot continue environment being created"
        exit 1
    fi
fi
echo -e "***********************************************************"
echo -e "Reading pip_packages.txt"
comment="#"
null=""

declare -a pip_pkgs=()
# read all lines in the pip_packages.txt file
while read -r line; do
    if [[ "${line::1}" == $comment || $line == $null ]]; then
        continue
    else
        pip_pkgs+=("$line")
    fi
done < ./env_setup/pkg_lists/pip_packages.txt

# activate the python environment
source ./env/bin/activate
# loop through all packages
for pkg in "${pip_pkgs[@]}" 
do 
    # check if the package is already installed
    if [ $(pip3 list | grep -c "$pkg") != 0 ]; then
        echo -e "$pkg --> \033[92mPresent\033[0m"
    # otherwise install the package
    else
        echo -e "$pkg --> \033[s\033[31mNot Present\033[0m"
        sleep 0.5
        echo -e "\033[u\033[s\033[0K\033[33mInstalling\033[0m"
        pip3 install $pkg > /dev/null
        if [ $(pip3 list | grep -c "$pkg") != 0 ]; then
            echo -e "\033[u\033[0K \033[92mInstalled\033[0m"
        else
            echo -e "\033[u\033[0K \033[31mFailed\033[0m"
        fi
    fi
done
# deactivate the python virtual environment
deactivate

echo -e "***********************************************************"
echo -e "Reading deb_packages.txt"

declare -a names=()
declare -a bins=()

IFS=","
# read each line of the deb_packages.txt file using the ',' as a delimiter
while read -r line; do
    if [[ "${line::1}" == $comment || $line == $null ]]; then
        continue
    else
        # store line items into the bin and name arrays
        read -ra tuple <<< $line
        names+=("${tuple[0]}")
        bins+=("${tuple[1]}")
    fi
done < ./env_setup/pkg_lists/deb_packages.txt

# loop through each item in the names list and check if it is present
for (( i=0 ; i<${#names[@]} ; ++i ));
do 
    if [ -f "./env/usr/bin/${bins[i]}" ]; then
        echo -e "${names[$i]} --> \033[92mPresent\033[0m"
    # otherwise install the deb package to the usr/bin directory
    else
        echo -e "${names[$i]} --> \033[s\033[31mNot Present\033[0m"
        sleep 0.5
        echo -e "\033[u\033[s\033[0K\033[33mInstalling\033[0m"
        
        #download the deb package using apt
        apt download ${names[$i]} > /dev/null 2>/dev/null
        
        #get the name of the deb package
        deb_package=$(find ./ -regex "./$($names[$i]).*.deb")
        #extract the files from the deb package into the /env/usr directory
        dpkg-deb -x $deb_package ./env

        #rm the deb package
        rm $deb_package

        # check that the package was installed to the correct directory (/env/bin)
        if [ -f "./env/usr/bin/${bins[i]}" ]; then
            echo -e "\033[u\033[0K\033 \033[92mInstalled\033[0m"
        else
            echo -e "\033[u\033[0K\033 \033[31mFailed\033[0m"
        fi
    fi
done

echo -e "***********************************************************"
echo -e "Reading .profile"
# get the path to the env/usr/bin
t_path=($(cd ./env/usr/bin && pwd))
# check if the exported path is in the .profile file
if [ $(grep -c "\$PATH:$t_path" ~/.profile) != 0 ]; then
    echo -e "environment path export --> \033[92mPresent\033[0m"

# otherwise append the export to the end of the .profile file
else
    echo -e "environment path export --> \033[s\033[31mNot Present\033[0m"
    sleep 0.5
    echo -e "\033[u\033[s\033[0K\033[33mAdding export\033[0m"
    echo -e "export PATH=\"\$PATH:$t_path\"" >> ~/.profile
    # update the users path by running the .profile file
    source ~/.profile
    echo -e "\033[u\033[0K \033[92mExport added\033[0m"
fi
echo -e "***********************************************************\n"
echo -e "==========================================================="
echo -e "Environment setup complete"
echo -e "==========================================================="