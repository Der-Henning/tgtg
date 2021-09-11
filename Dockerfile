FROM python:3.9-slim

WORKDIR /usr/src/app

RUN pip install --no-cache-dir tgtg python-pushsafer python-dotenv requests

COPY ./src .

CMD [ "python","-u","scanner.py" ]
