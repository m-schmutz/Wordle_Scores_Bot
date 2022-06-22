FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update -y && apt upgrade -y

WORKDIR /env

RUN apt install python3 -y \
    && apt install python3-pip -y

RUN pip3 install opencv-python \
    && pip3 install pytesseract \
    && pip3 install numpy \
    && pip3 install requests \
    && pip3 install discord \ 
    && pip3 install psutil \
    && pip3 install selenium 

RUN apt install tesseract-ocr -y \
    && apt install firefox-geckodriver -y \
    && apt install firefox -y

COPY . .

CMD python3 get_solution_word.py
