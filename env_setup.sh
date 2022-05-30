#!/bin/bash
echo "Beginning environment setup"
#check if environment exists
if [ -d "env" ];
then
echo "env installed"

#otherwise create new ./env
else
echo "installing python3-venv"
#install python3-venv
sudo apt install python3-venv

echo "Creating ./env environment"
#create virtual environment in current directory
python3 -m venv ./env
fi
#add any other binaries needed to run the script
#run as sudo apt install <dependancy>
sudo apt install tesseract-ocr

#go into python environment
source ./env/bin/activate

#add any other python dependancies below
#use pip3 install <package>
pip3 install opencv-python

pip3 install pytesseract

pip3 install numpy

pip3 install requests
