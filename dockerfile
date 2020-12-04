FROM python:3

WORKDIR /usr/src/app

RUN pip install --no-cache-dir tgtg python-pushsafer schedule

COPY . .

CMD [ "python","-u","./toogoodtogo.py" ]
