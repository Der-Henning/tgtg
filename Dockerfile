FROM python:3.9-slim

COPY requirements.txt /tmp/pip-tmp/

RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

WORKDIR /usr/src/app

COPY ./src .

CMD [ "python","-u","scanner.py" ]
