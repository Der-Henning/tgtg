FROM python:3.9

COPY requirements.txt /tmp/pip-tmp/
COPY requirements.dev.txt /tmp/pip-tmp/

RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.dev.txt \
    && rm -rf /tmp/pip-tmp

RUN mkdir -p /tokens
VOLUME /tokens
ENV TGTG_TOKEN_PATH=/tokens