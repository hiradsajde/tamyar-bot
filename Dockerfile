FROM python:3.10-slim 

WORKDIR /usr/src/app 

RUN apt update 
RUN apt install ffmpeg -y

COPY ./requirements.txt ./ 
RUN pip install --no-cache-dir -r requirements.txt 

COPY . . 

CMD ["python" , "-m" ,"cmd.main"]