#!/bin/bash
echo -e "==========================================================="
echo -e "Beginning Virtual Environment Setup"
echo -e "===========================================================\n"

echo -e "Checking that apt is up to date: \033[s"
sudo apt -y update -y > /dev/null 2> /dev/null && sudo apt upgrade -y > /dev/null 2> /dev/null
echo -e "\033[u\033[92mdone\033[0m"
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
    sudo apt install python3-venv > /dev/null 2> /dev/null
    python3 -m venv ./env > /dev/null

    if [ -d "env" ]; then 
        echo -e "\033[u\033[0K \033[92mInstalled\033[0m"

    else
        echo -e "\033[u\033[0K \033[31mFailed\033[0m"
    fi
fi
echo -e "***********************************************************"
echo -e "Reading pip_packages.txt"
comment="#"
null=""

declare -a pip_pkgs=()

while read -r line; do
    if [[ "${line::1}" == $comment || $line == $null ]]; then
        continue
    else
        pip_pkgs+=("$line")
    fi
done < ./env_setup/pkg_lists/pip_packages.txt


source ./env/bin/activate
for pkg in "${pip_pkgs[@]}" 
do 
    if [ $(pip3 list | grep -c "$pkg") != 0 ]; then
        echo -e "$pkg --> \033[92mPresent\033[0m"
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
deactivate

echo -e "***********************************************************"
echo -e "Reading deb_packages.txt"

declare -a names=()
declare -a bins=()

IFS=","
while read -r line; do
    if [[ "${line::1}" == $comment || $line == $null ]]; then
        continue
    else
        read -ra tuple <<< $line
        names+=("${tuple[0]}")
        bins+=("${tuple[1]}")
    fi
done < ./env_setup/pkg_lists/deb_packages.txt


for (( i=0 ; i<${#names[@]} ; ++i ));
do 
    if [ -f "./env/usr/bin/${bins[i]}" ]; then
        echo -e "${names[$i]} --> \033[92mPresent\033[0m"
    else
        echo -e "${names[$i]} --> \033[s\033[31mNot Present\033[0m"
        sleep 0.5
        echo -e "\033[u\033[s\033[0K\033[33mInstalling\033[0m"

        apt download ${names[$i]} > /dev/null 2>/dev/null
        
        deb_package=$(find ./ -regex "./$($names[$i]).*.deb")
        dpkg-deb -x $deb_package ./env

        rm $deb_package

        if [ -f "./env/usr/bin/${bins[i]}" ]; then
            echo -e "\033[u\033[0K\033 \033[92mInstalled\033[0m"
        else
            echo -e "\033[u\033[0K\033 \033[31mFailed\033[0m"
        fi
    fi
done

echo -e "***********************************************************"
echo -e "Reading .profile"
t_path=($(cd ./env/usr/bin && pwd))
if [ $(grep -c "\$PATH:$t_path" ~/.profile) != 0 ]; then
    echo -e "environment path export --> \033[92mPresent\033[0m"

else
    echo -e "environment path export --> \033[s\033[31mNot Present\033[0m"
    sleep 0.5
    echo -e "\033[u\033[s\033[0K\033[33mAdding export\033[0m"
    echo -e "export PATH=\"\$PATH:$t_path\"" >> ~/.profile
    source ~/.profile
    echo -e "\033[u\033[0K \033[92mExport added\033[0m"
fi
echo -e "***********************************************************\n"
echo -e "==========================================================="
echo -e "Environment setup complete"
echo -e "==========================================================="