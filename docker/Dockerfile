FROM python:3.11-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_WARN_SCRIPT_LOCATION=0 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1 \
    POETRY_INSTALLER_MAX_WORKERS=5
ENV TGTG_TOKEN_PATH=/tokens
ENV LOGS_PATH=/logs
ENV DOCKER=true
ENV UID=1000
ENV GID=1000
ENV PATH=/venv/bin:${PATH}

RUN apt-get update && apt-get upgrade -y

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

FROM base as builder

RUN apt-get install -y gcc libffi-dev g++ && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

WORKDIR /build
RUN pip install "poetry==${POETRY_VERSION}" poetry-plugin-bundle
RUN --mount=type=bind,target=. poetry bundle venv /venv

FROM base as final
COPY ./docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY --from=builder /venv /venv

RUN python -m tgtg_scanner -v

ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "python", "-m", "tgtg_scanner" ]
