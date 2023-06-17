FROM python:3.10-slim

RUN addgroup --gid 1001 tgtg && \
    adduser --shell /bin/false --disabled-password --uid 1001 --gid 1001 tgtg
RUN mkdir -p /app
RUN chown tgtg:tgtg /app
RUN mkdir -p /tokens
RUN chown tgtg:tgtg /tokens
ENV TGTG_TOKEN_PATH=/tokens
ENV DOCKER=true
ENV PYTHONUNBUFFERED=1

VOLUME /tokens
WORKDIR /app
USER tgtg

COPY --chown=tgtg:tgtg requirements.txt /tmp/pip-tmp/
RUN pip3 install --disable-pip-version-check --no-cache-dir \
    --no-warn-script-location -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

COPY --chown=tgtg:tgtg ./src .

CMD [ "python", "-u", "main.py" ]
