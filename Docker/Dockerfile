FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update -y
RUN apt upgrade -y

WORKDIR /env

RUN apt install python3 -y
RUN apt install python3-pip -y

RUN pip3 install opencv-python
RUN pip3 install pytesseract
RUN pip3 install numpy
RUN pip3 install requests
RUN pip3 install discord
RUN pip3 install psutil
RUN pip3 install selenium

RUN apt install tesseract-ocr -y
RUN apt install firefox-geckodriver -y
RUN apt install firefox -y

COPY . .

CMD python3 get_solution_word.py
