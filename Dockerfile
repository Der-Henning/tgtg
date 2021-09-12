FROM python:3.9-slim

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY ./src .

CMD [ "python","-u","scanner.py" ]
