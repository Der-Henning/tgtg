FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_WARN_SCRIPT_LOCATION=0 \
    PIP_ROOT_USER_ACTION=ignore \
    AIOHTTP_NO_EXTENSIONS=1 \
    MULTIDICT_NO_EXTENSIONS=1 \
    YARL_NO_EXTENSIONS=1
ENV TGTG_TOKEN_PATH=/tokens
ENV LOGS_PATH=/logs
ENV DOCKER=true
ENV UID=1000
ENV GID=1000

RUN addgroup --gid ${GID} tgtg && \
    adduser --shell /bin/false \
            --disabled-password \
            --uid ${UID} \
            --gid ${GID} \
            tgtg
RUN mkdir -p ${LOGS_PATH}
RUN mkdir -p ${TGTG_TOKEN_PATH}
RUN chown tgtg:tgtg ${LOGS_PATH}
RUN chown tgtg:tgtg ${TGTG_TOKEN_PATH}
VOLUME ${TGTG_TOKEN_PATH}

RUN --mount=type=bind,target=/context \
    pip install -r /context/requirements.txt && \
    pip install /context

COPY ./docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN python -m tgtg_scanner -v

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "python", "-m", "tgtg_scanner" ]
