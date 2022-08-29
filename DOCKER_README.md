# TGTG Scanner

Readme, source and documentation on [https://github.com/Der-Henning/tgtg](https://github.com/Der-Henning/tgtg).

## Supported Tags

 The `latest` images represent the latest stable release.
 The `edge` images contain the latest commits to the main branch.
 The `alpine` images are based on the alpine linux distribution and are significantly smaller.

- `edge`
- `edge-alpine`
- `v1`, `v1.11`, `v1.11.5`, `latest`
- `v1-alpine`, `v1.11-alpine`, `v1.11.5-alpine`, `latest-alpine`

## Docker Compose Example

````xml
version: "3.3"
services:
  app:
    image: derhenning/tgtg:latest
    environment: 
      - TZ=Europe/Berlin
      - DEBUG=false
      - TGTG_USERNAME=
      - SLEEP_TIME=60
      - ITEM_IDS=
      - METRICS=false
      - METRICS_PORT=8000
      - DISABLE_TESTS=false

      - SMTP=true
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
      #- TELEGRAM_BODY=

      - IFTTT=false
      - IFTTT_EVENT=tgtg_notification
      - IFTTT_KEY=

      - WEBHOOK=false
      - WEBHOOK_URL=
      - WEBHOOK_METHOD=POST
      - WEBHOOK_BODY=
      - WEBHOOK_TYPE=
      - WEBHOOK_TIMEOUT=60
    volumes:
      - tokens:/tokens
volumes:
  tokens:
````
