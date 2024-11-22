<!-- markdownlint-disable-next-line MD041 -->
## Basic configuration

The only required option is the Email aka Username to your TGTG account.

A minimalistic configuration could look like this:

```ini
[TGTG]
Username = my_mail@example.com
```

This config will start the scanner and lead you through the login process.
After the successful login, you will see changes in the available amounts of your favorite magic bags in the console window.

## Variables

Some of the following options allow the inclusion of special variables that contain item (magic bag) information.

Example to include the display name of the item: `${{display_name}}`

Variables with the `locale` property are affected by the `locale` option and returned in the given language.

| variable | description | example | locale |
|----------|-------------|---------|--------|
| item_id | unique identifier of the item | `774625` | |
| items_available | number of available items | `2` | |
| display_name | name of the item as in the APP | `Chutney Indian Food - Hamburg – Europapassage 2.OG` | |
| description | item description | `Rette eine Magic Bag mit leckerem indischen Essen.` | |
| price | item price | `3.20` | |
| value | item value | `9.60` | |
| currency | price/value currency | `EUR` | |
| pickupdate | formatted string | `tomorrow, 18:00 - 21:50` | YES |
| favorite | is favorite | `YES` or `NO` | |
| rating | overall rating | `3.3` | |
| buffet | is buffet | `YES` or `NO` | |
| item_category |  | `MEAL` | |
| item_name |  | | |
| packaging_option |  | `BAG_ALLOWED` | |
| pickup_location |  | `Ballindamm 40, 20095 Hamburg, Deutschland` | |
| store_name | | `Chutney Indian Food` | |
| item_logo | item logo url | `https://tgtg-mkt-cms-prod.s3.eu-west-1.amazonaws.com/13512/TGTG_Icon_White_Cirle_1988x1988px_RGB.png` | |
| item_cover | item cover url | `https://images.tgtg.ninja/standard_images/GENERAL/other1.jpg` | |
| scanned_on | timestamp when the item was scanned | `2023-02-14 20:43:21` | |
| item_logo_bytes | item logo as data blob | | |
| item_cover_bytes | item cover as data blob | | |
| link | url of the item | `https://share.toogoodtogo.com/item/774625` | |
| distance_walking | walking distance from home | `5.9 km` | YES |
| distance_driving | driving distance from home | `8 km` | YES |
| distance_transit | transit distance from home | `8 km` | YES |
| distance_biking | biking distance from home | `6.1 km` | YES |
| duration_walking | walking duration from home | `1 hour` | YES |
| duration_driving | driving duration from home | `20 minutes` | YES |
| duration_transit | transit duration from home | `45 minutes` | YES |
| duration_biking | biking duration from home | `30 minutes` | YES |

## Cron Scheduler

For formatting support see: <https://crontab.guru/#*_12-14_*_*_1-5>

You can combine multiple crons as semicolon separated list.

## Available options

### [MAIN] / general settings

| config.ini | environment | description | default |
|------------|-------------|-------------|---------|
| Debug | DEBUG | enable debugging mode | `false` |
| SleepTime | SLEEP_TIME | time between two consecutive scans in seconds | `60` |
| ScheduleCron | SCHEDULE_CRON | run only on schedule | `* * * * *` |
| ItemIDs | ITEM_IDS | **Depreciated!** comma-separated list of additional (none favorite) items to scan | |
| Metrics | METRICS | enable Prometheus metrics HTTP server | `false` |
| MetricsPort | METRICS_PORT | port for metrics server | `8000` |
| DisableTests | DISABLE_TESTS | disable test notifications on startup | `false` |
| Quiet | QUIET | minimal console output | `false` |
| Locale | LOCALE | localization | `en_US` |
| Activity | ACTIVITY | show running indicator (always disabled in docker) | `true` |
| | TZ | timezone for docker based setups, e.g. `Berlin/Europe` | |
| | UID | set user id for docker container | `1000` |
| | GID | set group id for docker container | `1000` |

### [TGTG] / TGTG account

| config.ini | environment | description | default | required |
|------------|-------------|-------------|---------|:----------:|
| Username | TGTG_USERNAME | email connected to your TGTG Account |  | YES |
| AccessToken | TGTG_ACCESS_TOKEN | TGTG API access token | | |
| RefreshToken | TGTG_REFRESH_TOKEN | TGTG API refresh token | | |
| Datadome | TGTG_DATADOME | TGTG API datadome protection cookie | | |
| Timeout | TGTG_TIMEOUT | timeout for API requests | `60` | |
| AccessTokenLifetime | TGTG_ACCESS_TOKEN_LIFETIME | access token lifetime in seconds | `14400` | |
| MaxPollingTries | TGTG_MAX_POLLING_TRIES | max polling retries during login | `24` | |
| PollingWaitTime | TGTG_POLLING_WAIT_TIME | time between polling retries in seconds | `5` | |

### [LOCATION] / Location settings

| config.ini | environment | description | default | required if enabled | variables |
|------------|-------------|-------------|---------|:-------------------:|:---------:|
| Enabled | LOCATION | enable location service | `false` | | |
| GoogleMapsAPIKey | LOCATION_GOOGLE_MAPS_API_KEY | API key for google maps service |  | YES | |
| OriginAddress | LOCATION_ORIGIN_ADDRESS | origin for distance calculation, e.g. your home address |  | YES | |

### [CONSOLE] / Console Notifier

| config.ini | environment | description | default | required if enabled | variables |
|------------|-------------|-------------|---------|:-------------------:|:---------:|
| Enabled | CONSOLE | enable console notifications | `false` | | |
| Body | CONSOLE_BODY | message body | `${{scanned_on}} ${{display_name}} - new amount: ${{items_available}}` | | YES |
| Cron | CONSOLE_CRON | enable notification only on schedule | `* * * * *` | | |

### [SMTP] / SMTP Notifier

| config.ini | environment | description | default | required if enabled | variables |
|------------|-------------|-------------|---------|:-------------------:|:---------:|
| Enabled | SMTP | enable SMTP notifications | `false` | | |
| Host | SMTP_HOST | SMTP server host | `smtp.gmail.com` | | |
| Port | SMTP_PORT | SMTP server port | `587` | | |
| TLS | SMTP_TLS | enable TLS | `true`| | |
| SSL | SMTP_SSL | enable SSL | `false` | | |
| Timeout | SMTP_TIMEOUT | set timeout in seconds | 60 | | |
| Username | SMTP_USERNAME | login username | | | |
| Password | SMTP_PASSWORD | login password | | | |
| Sender | SMTP_SENDER | email sender | | | |
| Recipients | SMTP_RECIPIENTS | email recipients | | YES | |
| RecipientsPerItem | SMTP_RECIPIENTS_PER_ITEM | email recipients per item as JSON `{"ItemId_1": ["mail@example.com", ...], ...}` | | | |
| Subject | SMTP_SUBJECT | email subject | `New Magic Bags` | | YES |
| Body | SMTP_BODY | email html body | `<b>${{display_name}}</b> </br> New Amount: ${{items_available}}` | | YES |
| Cron | SMTP_CRON | enable notification only on schedule | `* * * * *` | | |

### [PUSHSAFER] / Pushsafer Notifier

| config.ini | environment | description | default | required if enabled | variables |
|------------|-------------|-------------|---------|:-------------------:|:---------:|
| Enabled | PUSHSAFER | enable Pushsafer notifications | `false` | | |
| Key | PUSHSAFER_KEY | Pushsafer API key | | YES | |
| DeviceID | PUSHSAFER_DEVICE_ID | Pushsafer device ID | | YES | |
| Cron | PUSHSAFER_CRON | enable notification only on schedule | `* * * * *` | | |

### [IFTTT] / IFTTT Notifier

| config.ini | environment | description | default | required if enabled | variables |
|------------|-------------|-------------|---------|:-------------------:|:---------:|
| Enabled | IFTTT | enable IFTTT notifications | `false` | | |
| Event | IFTTT_EVENT | IFTTT webhook event |  | YES | |
| Key | IFTTT_KEY | IFTTT webhook key |  | YES | |
| Body | IFTTT_BODY | JSON message body | `{"value1": "${{display_name}}", "value2": ${{items_available}}, "value3": "${{link}}"}` | | YES |
| Timeout | IFTTT_TIMEOUT | timeout for API requests | 60 | | |
| Cron | IFTTT_CRON | enable notification only on schedule | `* * * * *` | | |

### [TELEGRAM] / Telegram Notifier

| config.ini | environment | description | default | required if enabled | variables |
|------------|-------------|-------------|---------|:-------------------:|:---------:|
| Enabled | TELEGRAM | enable Telegram notifications | `false` | | |
| Token | TELEGRAM_TOKEN | Telegram Bot token | | YES | |
| ChatIDs | TELEGRAM_CHAT_IDS | comma-separated list of chat ids | | | |
| Body | TELEGRAM_BODY | message body | `*${{display_name}}* \n*Available*: ${{items_available}}\n*Price*: ${{price}} ${{currency}}\n*Pickup*: ${{pickupdate}}` | | YES |
| DisableCommands | TELEGRAM_DISABLE_COMMANDS | disable bot commands | `false` | | |
| OnlyReservations | TELEGRAM_ONLY_RESERVATIONS | only send notifications for reservations | `false` | | |
| Timeout | TELEGRAM_TIMEOUT | timeout for telegram API requests | 60 | | |
| Cron | TELEGRAM_CRON | enable notification only on schedule | `* * * * *` | | |

#### Note on Markdown V2

As of Version 1.17.0 the Telegram Notifier uses the Markdown V2 parser of the Telegram API.
This requires all special markdown characters, that should not be parsed as markdown commands,
to be escaped with a preceding `\`.
The special characters are `_`, `*`, `[`, `]`, `(`, `)`, `~`, `` ` ``, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.` and `!`.

### [APPRISE] / Apprise Notifier

For details on the service URL configuration see <https://github.com/caronc/apprise>.

| config.ini | environment | description | default | required if enabled | variables |
|------------|-------------|-------------|---------|:-------------------:|:---------:|
| Enabled | APPRISE | enable Apprise notifications | `false` | | |
| URL | APPRISE_URL | Service URL | | YES | |
| Title | APPRISE_TITLE | Notification title | `New Magic Bags` | | YES |
| Body | APPRISE_BODY | Notification body | `${{display_name}} - new amount: ${{items_available}} - ${{link}}` | | YES |
| Cron | APPRISE_CRON | enable notification only on schedule | `* * * * *` | | |

### [NTFY] / Ntfy Notifier

| config.ini | environment | description | default | required if enabled | variables |
|------------|-------------|-------------|---------|:-------------------:|:---------:|
| Enabled | NTFY | enable Ntfy notifications | `false` | | |
| Server | NTFY_SERVER | Ntfy server URL | `https://ntfy.sh` | YES | |
| Topic | NTFY_TOPIC | Ntfy topic | | YES | |
| Title | NTFY_TITLE | Notification title | `New TGTG items` | | YES |
| Message | NTFY_MESSAGE | Notification message | `${{display_name}} - New Amount: ${{items_available}} - ${{itelinkm_id}}` | | YES |
| Priority | NTFY_PRIORITY | | `default` | | |
| Tags | NTFY_TAGS | comma-separated list of tags | `shopping,tgtg` | | YES |
| Click | NTFY_CLICK | URL to open on click | `${{link}}` | | YES |
| Username | NTFY_USERNAME | auth username | | | |
| Password | NTFY_PASSWORD | auth password | | | |
| Token | NTFY_TOKEN | auth token, only used if username and password are empty | | | |
| Timeout | NTFY_TIMEOUT | timeout for Ntfy requests | 60 | | |
| Cron | NTFY_CRON | enable notification only on schedule | `* * * * *` | | |

### [WEBHOOK] / Webhook Notifier

| config.ini | environment | description | default | required if enabled | variables |
|------------|-------------|-------------|---------|:-------------------:|:---------:|
| Enabled | WEBHOOK | enable Webhook notifications | `false` | | |
| URL | WEBHOOK_URL | webhook endpoint | | YES | |
| Method | WEBHOOK_METHOD | request method | `POST` | | |
| Body | WEBHOOK_BODY | request body | `''` | | YES |
| Type | WEBHOOK_TYPE | request content type | `text/plain` | | |
| Headers | WEBHOOK_HEADERS | additional request headers as JSON | `{}` | | |
| Username | WEBHOOK_USERNAME | basic authentication username | | | |
| Password | WEBHOOK_PASSWORD | basic authentication password | | | |
| Timeout | WEBHOOK_TIMEOUT | request timeout | `60` | | |
| Cron | WEBHOOK_CRON | enable notification only on schedule | `* * * * *` | | |

### [DISCORD] / Discord Notifier

| config.ini | environment | description | default | required if enabled | variables |
|------------|-------------|-------------|---------|:-------------------:|:---------:|
| Enabled | DISCORD | enable Discord notifications | `false` | | |
| Prefix | DISCORD_PREFIX | Prefix, that bot should react to | `!` | | |
| Token | DISCORD_TOKEN | auth token | | YES | |
| Channel | DISCORD_CHANNEL | enable Discord notifications | | | |
| Body | DISCORD_BODY | Notification body | `*${{display_name}}*\n*Available*: ${{items_available}}\n*Price*: ${{price}} ${{currency}}\n*Pickup*: ${{pickupdate}}` | | YES |
| DisableCommands | DISCORD_DISABLE_COMMANDS | disable bot commands | `false` | | |
| Cron | DISCORD_CRON | enable notification only on schedule | `* * * * *` | | |

#### Setting up a Discord Bot

Register an application and associated bot user for use with TGTG scanner at <https://discord.com/developers/applications>.
For details on how to set up see
<https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-the-developer-portal>.
The bot will send notifications to a specific channel. To obtain the channel ID, see
<https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID>.
