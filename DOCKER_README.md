# Quick reference

Readme, source, and documentation on [https://github.com/Der-Henning/tgtg](https://github.com/Der-Henning/tgtg).

# Supported Tags and respective `Dockerfile` links

 The `latest` images represent the latest stable release.
 The `edge` images contain the latest commits to the main branch.
 The `alpine` images are based on the alpine Linux distribution and are significantly smaller.

- [`edge`](https://github.com/Der-Henning/tgtg/blob/main/Dockerfile)
- [`edge-alpine`](https://github.com/Der-Henning/tgtg/blob/main/Dockerfile.alpine)
- [`v1`, `v1.15`, `v1.15.2`, `latest`](https://github.com/Der-Henning/tgtg/blob/v1.15.2/Dockerfile)
- [`v1-alpine`, `v1.15-alpine`, `v1.15.2-alpine`, `latest-alpine`](https://github.com/Der-Henning/tgtg/blob/v1.15.2/Dockerfile.alpine)

# Quick Start

**Docker Compose Example:**

````xml
version: "3.3"

services:
  tgtg:
    image: derhenning/tgtg:latest
    environment:
      - TZ=Europe/Berlin
      - DEBUG=false
      - TGTG_USERNAME=
      - SLEEP_TIME=60
      #- SCHEDULE_CRON=
      #- ITEM_IDS=
      - METRICS=false
      - METRICS_PORT=8000
      - DISABLE_TESTS=false
      - QUIET=false
      - LOCALE=en_US

      - APPRISE=false
      - APPRISE_URL=
      - APPRISE_BODY=
      #- APPRISE_TITLE=
      #- APPRISE_CRON=

      - SMTP=false
      - SMTP_HOST=smtp.gmail.com
      - SMTP_PORT=465
      - SMTP_USERNAME=max.mustermann@gmail.com
      - SMTP_PASSWORD=
      - SMTP_TLS=true
      - SMTP_SENDER=max.mustermann@gmail.com
      - SMTP_RECIPIENT=max.mustermann@gmail.com
      #-SMTP_SUBJECT=
      #-SMTP_BODY=

      - PUSH_SAFER=false
      - PUSH_SAFER_KEY=
      - PUSH_SAFER_DEVICE_ID=

      - TELEGRAM=false
      - TELEGRAM_TOKEN=
      - TELEGRAM_CHAT_IDS=
      #- TELEGRAM_TIMEOUT=60
      #- TELEGRAM_BODY=

      - IFTTT=false
      - IFTTT_EVENT=tgtg_notification
      - IFTTT_KEY=

      - WEBHOOK=false
      - WEBHOOK_URL=
      - WEBHOOK_METHOD=POST
      - WEBHOOK_BODY=
      - WEBHOOK_TYPE=plain/text
      #- WEBHOOK_HEADERS=
      #- WEBHOOK_TIMEOUT=60
      #- WEBHOOK_CRON=
    volumes:
      - tokens:/tokens

volumes:
  tokens:
````
