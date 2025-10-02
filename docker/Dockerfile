ARG PYTHON_VERSION=3.13

FROM python:${PYTHON_VERSION} AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_WARN_SCRIPT_LOCATION=0 \
    PIP_ROOT_USER_ACTION=ignore \
    AIOHTTP_NO_EXTENSIONS=1 \
    MULTIDICT_NO_EXTENSIONS=1 \
    YARL_NO_EXTENSIONS=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y build-essential

RUN --mount=type=bind,target=/context \
    python -m venv /opt/venv && \
    pip install -r /context/requirements.txt && \
    pip install /context

FROM python:${PYTHON_VERSION}-slim

ENV TGTG_TOKEN_PATH=/tokens \
    LOGS_PATH=/logs \
    DOCKER=true \
    UID=1000 \
    GID=1000 \
    PATH="/opt/venv/bin:$PATH"

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

COPY ./docker/entrypoint.sh /entrypoint.sh
COPY --from=builder /opt/venv /opt/venv

RUN python -m tgtg_scanner -v

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "python", "-m", "tgtg_scanner" ]
