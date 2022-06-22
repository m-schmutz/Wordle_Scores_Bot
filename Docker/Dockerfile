FROM ubuntu:20.04

RUN apt update -y
RUN apt upgrade -y

RUN apt install python3 -y

COPY hello.py ./hello.py

RUN chmod +x ./hello.py

CMD python3 hello.py