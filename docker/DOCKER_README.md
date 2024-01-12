# Quick reference

Readme, source, and documentation on [https://github.com/Der-Henning/tgtg](https://github.com/Der-Henning/tgtg).

<!-- markdownlint-disable-next-line MD025 -->
# Supported Tags and respective `Dockerfile` links

 The `latest` images represent the latest stable release.
 The `edge` images contain the latest commits to the main branch.
 The `alpine` images are based on the alpine Linux distribution and are significantly smaller.

- [`edge`](https://github.com/Der-Henning/tgtg/blob/main/docker/Dockerfile)
- [`edge-alpine`](https://github.com/Der-Henning/tgtg/blob/main/docker/Dockerfile.alpine)
- [`${MAJOR_VERSION}`, `${MINIOR_VERSION}`, `${FULL_VERSION}`, `latest`](https://github.com/Der-Henning/tgtg/blob/${FULL_VERSION}/docker/Dockerfile)
- [`${MAJOR_VERSION}-alpine`, `${MINIOR_VERSION}-alpine`, `${FULL_VERSION}-alpine`, `latest-alpine`](https://github.com/Der-Henning/tgtg/blob/${FULL_VERSION}/docker/Dockerfile.alpine)

<!-- markdownlint-disable-next-line MD025 -->
# Quick Start

**Docker Compose Example:**

Basic example using Telegram notifications.

For more options and details visit <https://github.com/Der-Henning/tgtg/wiki/Configuration>.

````xml
version: '3.3'

services:
  scanner:
    image: derhenning/tgtg:latest-alpine

    environment:
    - TGTG_USERNAME=
    - SLEEP_TIME=60
    - TZ=Europe/Berlin
    - LOCALE=de_DE

    - TELEGRAM=true
    - TELEGRAM_TOKEN=
    - TELEGRAM_CHAT_IDS=

    volumes:
    - tokens:/tokens

volumes:
  tokens:
````
