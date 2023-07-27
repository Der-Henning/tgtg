FROM python:3.10-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/venv"
ENV TGTG_TOKEN_PATH=/tokens
ENV LOGS_PATH=/logs
ENV DOCKER=true
ENV POETRY_VERSION=1.5.1
ENV UID=1000
ENV GID=1000

RUN addgroup --gid $GID tgtg && \
    adduser --shell /bin/false --disabled-password --uid $UID --gid $GID tgtg
RUN mkdir -p /logs
RUN mkdir -p /tokens
RUN chown tgtg:tgtg /tokens
RUN chown tgtg:tgtg /logs
VOLUME /tokens
RUN apt-get update && apt-get upgrade -y

# Build dependencies
FROM base as builder
RUN pip install --upgrade pip setuptools wheel && \
    pip install "poetry==$POETRY_VERSION" poetry-plugin-bundle
WORKDIR $PYSETUP_PATH
COPY . .
RUN poetry install --without test,build && \
    poetry bundle venv $VENV_PATH

# Create Production Image
FROM base as production
ENV PATH="$VENV_PATH/bin:$PATH"
COPY ./docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY --from=builder $VENV_PATH $VENV_PATH
ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "python", "-m", "tgtg_scanner" ]