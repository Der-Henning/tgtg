# TGTG Scanner

[![Tests](https://github.com/Der-Henning/tgtg/actions/workflows/tests.yml/badge.svg)](https://github.com/Der-Henning/tgtg/actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/Der-Henning/tgtg/branch/main/graph/badge.svg?token=POHW9USW7C)](https://codecov.io/github/Der-Henning/tgtg)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/der-henning/tgtg/release.yml)](https://github.com/Der-Henning/tgtg/actions/workflows/release.yml)
[![GitHub release](https://img.shields.io/github/release/Der-Henning/tgtg?include_prereleases=&sort=semver&color=blue)](https://github.com/Der-Henning/tgtg/releases/)
[![Docker Pulls](https://img.shields.io/docker/pulls/derhenning/tgtg)](https://hub.docker.com/r/derhenning/tgtg)

TGTG Scanner observes your favorite TGTG Magic Bags for newly available items and notifies you
via mail, IFTTT, Ntfy, Telegram, PushSafer, Apprise or any other WebHook.
Notifications will be sent when the available amount of Magic Bags rises from zero to something.

Additionally, the currently available amounts can be provided via an HTTP server.

Running in a docker container the scanner can be seamlessly integrated with
OpenHab, Prometheus, and other automation, notification, and visualization services.

This software is provided as is without warranty of any kind.
If you have problems, find bugs, or have suggestions for improvement
feel free to create an issue or contribute to the project.
Before creating an issue please refer to the [FAQ](https://github.com/Der-Henning/tgtg/wiki/FAQ).

## Disclaimer

This Project is not affiliated, associated, authorized, endorsed by, or in any way
officially connected with Too Good To Go, or any of its subsidiaries or its affiliates.

Too Good To Go explicitly forbids the use of their platform the way this tool does if you use it.
In their Terms and Conditions, it says:
"The Consumer must not misuse the Platform (including hacking or 'scraping')."

If you use this tool you do it at your own risk.
Too Good To Go may stop you from doing so by (temporarily) blocking your access
and may even delete your account.

## Error 403

If you see the Error 403 in your logs please refer to the
[FAQ](https://github.com/Der-Henning/tgtg/wiki/FAQ#1-i-am-getting-error-403-all-the-time).

## Installation

You can install this tool on any computer.
For 24/7 notifications I recommended an installation on a NAS like Synology or a Raspberry Pi.
You can also try to use a virtual cloud server.

If you have any problems or questions feel free to create an issue.

For configuration options please refer to the projects wiki:
[Configuration](https://github.com/Der-Henning/tgtg/wiki/Configuration)

You have the following three options to install the scanner, ascending in complexity:

### Use a prebuilt binary

This is the simplest but least flexible solution suitable for most operating systems.

The binaries are built for latest Ubuntu, MacOS, and Windows running on an `x64` architecture.
If you are using another architecture like `arm` (e.g. RaspberryPi, Synology, etc.)
you have to run from source, compile the binary yourself or use the docker images.

1. Download latest [Releases](https://github.com/Der-Henning/tgtg/releases) for your OS
2. Unzip the archive
3. Edit `config.ini` as described in the [Wiki](https://github.com/Der-Henning/tgtg/wiki/Configuration)
4. Run the scanner

You can run the scanner manually if you need it, add it to your startup or create a system service.

The executables for Windows and MacOS are not signed by Microsoft and Apple,
which would be very expensive.
On MacOS, you have to hold the control key while opening the file and on Windows,
you have to confirm the displayed dialog.

### Run with Docker

My preferred method for servers, NAS, and RapsberryPis is using the pre-build multi-arch Linux images available via
[Docker Hub](https://hub.docker.com/r/derhenning/tgtg).
The images are built for Linux on `amd64`, `arm64`, `armv7`, `armv6`, and `i386`.

1. Install Docker and docker-compose
2. Copy and edit `docker-compose.yml` as described in the
[Wiki](https://github.com/Der-Henning/tgtg/wiki/Configuration)
3. Run `docker-compose up -d`

The container automatically creates a volume mounting `\tokens`
where the app saves the TGTG credentials after login.
These credentials will be reused at every start of the container to avoid the mail login process.
To log in with a different account you have to delete the created volume or the files in it.

To update the running container to the latest version of the selected tag run

```bash
docker-compose pull
docker-compose up -d
```

### Install as package

1. Install Git, Python>=3.9 and pip
2. Run `pip install git+https://github.com/Der-Henning/tgtg`
3. Create `config.ini` as described in the
[Wiki](https://github.com/Der-Henning/tgtg/wiki/Configuration)
4. Start scanner with `python -m tgtg_scanner`

To update to the latest release run
`pip install --upgrade git+https://github.com/Der-Henning/tgtg`.

If you receive the `ModuleNotFoundError: No module named '_ctypes'`
you may need to install `libffi-dev`.

### Run from source

Method for advanced usage.

1. Install Git, Python>=3.9 and poetry
2. Clone the repository `git clone https://github.com/Der-Henning/tgtg`
3. Enter repository folder `cd tgtg`
4. Run `poetry install --without test,build`
5. Create config file `cp config.sample.ini config.ini`
6. Modify `config.ini` as described in the
[Wiki](https://github.com/Der-Henning/tgtg/wiki/Configuration)
7. Run `poetry run scanner`

Alternatively, you can use environment variables as described in the wiki.
The scanner will look for environment variables if no `config.ini` is present.

To update to the latest release run `git pull`.

If you receive the `ModuleNotFoundError: No module named '_ctypes'`
you may need to install `libffi-dev`.

### Build your own binary

You could also build your own binary for your OS/Arch combination.

1. Clone the repository as described above
2. Run `poetry install --without test`
3. Run `make executable`

You will find the bundled binary including the `config.ini` in the `./dist` directory.

## Usage

When the scanner is started it will first try to log in to your TGTG account.
Similar to logging in to the TGTG app, you have to click on the link sent to you by mail.
This won't work on your mobile phone if you have installed the TGTG app,
so you have to check your mailbox on your PC.

After a successful login, the scanner will send a test notification on all configured notifiers.
If you don't receive any notifications, please check your configuration.

### Helper functions

The executable or the `tgtg_scanner/__main__.py` contains some useful helper functions that can be
accessed via optional command line arguments.
Running `scanner[.exe] --help`, `poetry run scanner --help`, `python tgtg_scanner/__main__.py --help`
or `python -m tgtg_scanner --help` displays the available commands.

<!-- markdownlint-disable MD013 -->
```txt
usage: scanner [-h] [-v] [-d] [-c config_file] [-l log_file] [-t | -f | -F | -a item_id [item_id ...] | -r item_id [item_id ...] | -R] [-j | -J] [--base_url BASE_URL]

Notifications for Too Good To Go

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -d, --debug           activate debugging mode
  -c config_file, --config config_file
                        path to config file (default: config.ini)
  -l log_file, --log_file log_file
                        path to log file (default: scanner.log)
  -t, --tokens          display your current access tokens and exit
  -f, --favorites       display your favorites and exit
  -F, --favorite_ids    display the item ids of your favorites and exit
  -a item_id [item_id ...], --add item_id [item_id ...]
                        add item ids to favorites and exit
  -r item_id [item_id ...], --remove item_id [item_id ...]
                        remove item ids from favorites and exit
  -R, --remove_all      remove all favorites and exit
  -j, --json            output as plain json
  -J, --json_pretty     output as pretty json
  --base_url BASE_URL   Overwrite TGTG API URL for testing
```
<!-- markdownlint-enable MD013 -->

Example (Unix only):

```bash
poetry run scanner -f -J >> items.json
```

Creates a formatted JSON file containing all your favorite items and their available information.

### Metrics

Enabling the metrics option will expose an HTTP server on the specified port supplying the currently available items.
You can scrape the data with Prometheus to create and visualize historic data or use it with your home automation.

Scrape config:

```xml
- job_name: 'TGTG'
  scrape_interval: 1m
  scheme: http
  metrics_path: /
  static_configs:
  - targets:
    - 'localhost:8000'
```

## Development

For development, I recommend using docker.

If you are developing with VSCode, you can open the project in the configured
development container including all required dependencies.

Alternatively, install all required development environment dependencies, including linting, testing, and building by executing

```bash
make install
```

For developement and testing it is sometimes usefull to trigger TGTG Magic Bag events.
For this purpose you can run the TGTG dev API proxy server.
The proxy redirects all requests to the official TGTG API server.
The responses from the item endpoint are modified by randomizing the amount of available magic bags.

```bash
make server
```

### Makefile commands

- `make install` installs development dependencies and pre-commit hooks
- `make server` starts TGTG dev API proxy server
- `make start` runs the scanner with debugging and using the API proxy
- `make test` runs unit tests
- `make lint` run pre-commit hooks including linting and code checks
- `make executable` creates a bundled executable in `/dist`
- `make images` builds docker images with tag `tgtg-scanner:latest` and `tgtg-scanner:latest-alpine`

### Creating new notifiers

Feel free to create and contribute new notifiers for other services and endpoints.
You can use an existing notifier as a template or build upon the webhook notifier.
E.g. see the [ifttt notifier](https://github.com/Der-Henning/tgtg/blob/main/src/notifiers/ifttt.py).

---
If you want to support me, feel free to buy me a coffee.

<!-- markdownlint-disable MD033 -->
<a href="https://www.buymeacoffee.com/henning" target="_blank">
<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="200">
</a>
