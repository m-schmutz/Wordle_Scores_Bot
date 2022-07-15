# Base image
FROM ubuntu:20.04

# Make image noninteractive
ENV DEBIAN_FRONTEND=noninteractive

#use server version of ubuntu
RUN apt-get update && apt-get install -y ubuntu-server

WORKDIR /bot

RUN apt install python3 -y && apt install python3-pip -y

CMD echo 'df -h'