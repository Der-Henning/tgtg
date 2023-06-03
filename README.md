[![Tests](https://github.com/Der-Henning/tgtg/actions/workflows/tests.yml/badge.svg)](https://github.com/Der-Henning/tgtg/actions/workflows/tests.yml)
[![codecov](https://codecov.io/github/Der-Henning/tgtg/branch/main/graph/badge.svg?token=POHW9USW7C)](https://codecov.io/github/Der-Henning/tgtg)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/der-henning/tgtg/release.yml)](https://github.com/Der-Henning/tgtg/actions/workflows/release.yml)
[![GitHub release](https://img.shields.io/github/release/Der-Henning/tgtg?include_prereleases=&sort=semver&color=blue)](https://github.com/Der-Henning/tgtg/releases/)
[![Docker Pulls](https://img.shields.io/docker/pulls/derhenning/tgtg)](https://hub.docker.com/r/derhenning/tgtg)

# TGTG Scanner

TGTG Scanner observes your favorite TGTG Magic Bags for newly available items and notifies you via mail, IFTTT, Ntfy, Telegram, PushSafer, Apprise or any other WebHook. Notifications will be sent when the available amount of Magic Bags rises from zero to something.

Additionally, the currently available amounts can be provided via an HTTP server.

Running in a docker container the scanner can be seamlessly integrated with OpenHab, Prometheus, and other automation, notification, and visualization services.

This software is provided as is without warranty of any kind. If you have problems, find bugs, or have suggestions for improvement feel free to create an issue or contribute to the project. Before creating an issue please refer to the [FAQ](https://github.com/Der-Henning/tgtg/wiki/FAQ).

## Disclaimer

This Project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Too Good To Go, or any of its subsidiaries or its affiliates.

Too Good To Go explicitly forbids the use of their platform the way this tool does if you use it. In their Terms and Conditions, it says: "The Consumer must not misuse the Platform (including hacking or 'scraping')."

If you use this tool you do it at your own risk. Too Good To Go may stop you from doing so by (temporarily) blocking your access and may even delete your account.

## Error 403

If you see the Error 403 in your logs please refer to the [FAQ](https://github.com/Der-Henning/tgtg/wiki/FAQ#1-i-am-getting-error-403-all-the-time).

## Installation

You can install this tool on any computer. For 24/7 notifications I recommended an installation on a NAS like Synology or a Raspberry Pi. You can also try to use a virtual cloud server.

If you have any problems or questions feel free to create an issue.

For configuration options please refer to the projects wiki: [Configuration](https://github.com/Der-Henning/tgtg/wiki/Configuration)

You have the following three options to install the scanner, ascending in complexity:

### Use a prebuilt binary

This is the simplest but least flexible solution suitable for most operating systems.

The binaries are built for latest Ubuntu, MacOS, and Windows running on an `x64` architecture. If you are using another architecture like `arm` (e.g. RaspberryPi, Synology, etc.) you have to run from source, compile the binary yourself or use the docker images.

1. Download latest [Releases](https://github.com/Der-Henning/tgtg/releases) for your OS
2. Unzip the archive
3. Edit `config.ini` as described in the [Wiki](https://github.com/Der-Henning/tgtg/wiki/Configuration)
4. Run the scanner

You can run the scanner manually if you need it, add it to your startup or create a system service.

The executables for Windows and MacOS are not signed by Microsoft and Apple, which would be very expensive.
On MacOS, you have to hold the control key while opening the file and on Windows, you have to confirm the displayed dialog.

### Run with Docker

My preferred method for servers, NAS, and RapsberryPis is using the pre-build multi-arch Linux images available via [Docker Hub](https://hub.docker.com/r/derhenning/tgtg). The images are built for Linux on `amd64`, `arm64`, `armv7`, `armv6`, and `i386`.

1. Install Docker and docker-compose
2. Copy and edit `docker-compose.yml` as described in the [Wiki](https://github.com/Der-Henning/tgtg/wiki/Configuration)
3. Run `docker-compose up -d`

The container automatically creates a volume mounting `\tokens` where the app saves the TGTG credentials after login. These credentials will be reused at every start of the container to avoid the mail login process. To log in with a different account you have to delete the created volume or the files in it.

To update the running container to the latest version of the selected tag run

````bash
docker-compose pull
docker-compose up -d
````

### Run from source

Method for advanced usage.

1. Install Git, Python>=3.9, and pip
2. Clone the repository `git clone https://github.com/Der-Henning/tgtg`
3. Enter repository folder `cd tgtg`
4. Run `pip install -r requirements.txt`
5. Create config file `cp src/config.sample.ini src/config.ini`
6. Modify `src/config.ini` as described in the [Wiki](https://github.com/Der-Henning/tgtg/wiki/Configuration)
7. Run `python src/main.py`

Alternatively, you can use environment variables as described in the `sample.env` file. The scanner will look for environment variables if no `config.ini` is present.

To update to the latest release run `git pull`.

If you receive the `ModuleNotFoundError: No module named '_ctypes'` you may need to install `libffi-dev`.

### Build your own binary

You could also build your own binary for your OS/Arch combination.

1. Clone the repository as described above
2. Run `pip install -r requirements-build.txt`
3. Run `make executable` or `pyinstaller scanner.spec`

You will find the bundled binary including the `config.ini` in the `./dist` directory.

## Usage

When the scanner is started it will first try to log in to your TGTG account. Similar to logging in to the TGTG app, you have to click on the link sent to you by mail. This won't work on your mobile phone if you have installed the TGTG app, so you have to check your mailbox on your PC.

After a successful login, the scanner will send a test notification on all configured notifiers. If you don't receive any notifications, please check your configuration.

### Helper functions

The executable or the `src/main.py` contains some useful helper functions that can be accessed via optional command line arguments. Running `scanner[.exe] --help` or `python src/main.py --help` displays the available commands.

````
usage: main.py [-h] [-v] [-d] [-t | -f | -F | -a item_id [item_id ...] | -r item_id [item_id ...] | -R] [-j | -J]

TooGoodToGo scanner and notifier.

options:
  -h, --help            show this help message and exit
  -v, --version         shows the program's version number and exit
  -d, --debug           activate debugging mode
  -t, --tokens          display your current access tokens and exit
  -f, --favorites       display your favorites and exit
  -F, --favorite_ids    display the item ids of your favorites and exit
  -a item_id [item_id ...], --add item_id [item_id ...]
                        add item ids to favorites and exit
  -r item_id [item_id ...], --remove item_id [item_id ...]
                        remove item ids from favorites and exit
  -R, --remove_all      remove all favorites and exit
  -j, --json            output as plain JSON
  -J, --json_pretty     output as pretty JSON
````

Example (Unix only):

````bash
python src/main.py -f -J >> items.json
````

Creates a formatted JSON file containing all your favorite items and their available information.

### Metrics

Enabling the metrics option will expose an HTTP server on the specified port supplying the currently available items. You can scrape the data with Prometheus to create and visualize historic data or use it with your home automation.

Scrape config:

````xml
  - job_name: 'TGTG'
    scrape_interval: 1m
    scheme: http
    metrics_path: /
    static_configs:
    - targets:
      - 'localhost:8000'
````

## Development

For development, I recommend using docker.

If you are developing with VSCode, you can open the project in the configured development container including all required dependencies.

Alternatively, install all required development environment dependencies, including linting, testing, and building by executing

````bash
pip install -r requirements-dev.txt
````

### Makefile commands

- `make image` builds docker image with tag `tgtg-scanner:latest`
- `make install` installs development dependencies
- `make start` is short for `python src/main.py`
- `make bash` starts dev python docker image with installed dependencies and mounted project in bash
- `make executable` creates a bundled executable in `/dist`
- `make test` runs unit tests
- `make lint` run pre-commit hooks
- `make clean` cleans up docker-compose

### Creating new notifiers

Feel free to create and contribute new notifiers for other services and endpoints. You can use an existing notifier as a template or build upon the webhook notifier. E.g. see the [ifttt notifier](https://github.com/Der-Henning/tgtg/blob/main/src/notifiers/ifttt.py).

---
If you want to support me, feel free to buy me a coffee.

<a href="https://www.buymeacoffee.com/henning" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="200"></a>
