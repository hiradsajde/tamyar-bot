FROM ubuntu:24.04

WORKDIR /usr/src/app 

RUN apt update 
RUN apt install ffmpeg python3 python3-pip wget curl -y

COPY ./requirements.txt ./ 

RUN pip install --break-system-packages -r requirements.txt 

COPY . . 

RUN wget git.io/warp.sh

ENTRYPOINT ["./entrypoint.sh"]