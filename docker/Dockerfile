FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_WARN_SCRIPT_LOCATION=0
ENV TGTG_TOKEN_PATH=/tokens
ENV LOGS_PATH=/logs
ENV DOCKER=true
ENV UID=1000
ENV GID=1000

RUN addgroup --gid $GID tgtg && \
    adduser --shell /bin/false \
            --disabled-password \
            --uid $UID \
            --gid $GID \
            tgtg
RUN mkdir -p /logs
RUN mkdir -p /tokens
RUN chown tgtg:tgtg /tokens
RUN chown tgtg:tgtg /logs
VOLUME /tokens

RUN --mount=type=bind,target=/context \
    pip install -r /context/docker/requirements.txt && \
    pip install /context

COPY ./docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN python -m tgtg_scanner -v

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "python", "-m", "tgtg_scanner" ]
