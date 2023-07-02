FROM python:3.10-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"
ENV PATH="$VENV_PATH/bin:$PATH"
ENV TGTG_TOKEN_PATH=/tokens
ENV LOGS_PATH=/logs
ENV DOCKER=true
ENV POETRY_VERSION=1.5.1
ENV UID=1000
ENV GID=1000

RUN addgroup --gid $GID tgtg && \
    adduser --shell /bin/false --disabled-password --uid $UID --gid $GID tgtg
RUN mkdir -p /app
RUN mkdir -p /logs
RUN mkdir -p /tokens
RUN chown tgtg:tgtg /tokens
RUN chown tgtg:tgtg /logs
VOLUME /tokens

# Build dependencies
FROM base as builder
RUN pip install "poetry==$POETRY_VERSION"
WORKDIR $PYSETUP_PATH
COPY ./poetry.lock ./pyproject.toml ./README.md ./
COPY ./src ./src
RUN poetry install --without test,build

# Create Production Image
FROM base as production
COPY ./docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY --from=builder $VENV_PATH $VENV_PATH
COPY ./src /app
ENTRYPOINT [ "/entrypoint.sh" ]
WORKDIR /app
CMD [ "python", "main.py" ]
