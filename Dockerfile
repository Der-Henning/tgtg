FROM python:3.10-slim as python-base

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
ENV DOCKER=true
ENV POETRY_VERSION=1.5.1

RUN addgroup --gid 1001 tgtg && \
    adduser --shell /bin/false --disabled-password --uid 1001 --gid 1001 tgtg
RUN mkdir -p /app
RUN chown tgtg:tgtg /app
RUN mkdir -p /tokens
RUN chown tgtg:tgtg /tokens
VOLUME /tokens

# Build dependencies
FROM python-base as builder
RUN apt-get update && \
    apt-get install --no-install-recommends -y build-essential
RUN pip install "poetry==$POETRY_VERSION"
WORKDIR $PYSETUP_PATH
COPY ./poetry.lock ./pyproject.toml ./
RUN poetry install --without test,build

# Create Production Image
FROM python-base as production
COPY --from=builder $VENV_PATH $VENV_PATH
COPY --chown=tgtg:tgtg ./src /app
WORKDIR /app
USER tgtg
CMD [ "python", "-u", "main.py" ]
