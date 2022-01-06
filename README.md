[![Publish multi-arch Docker images](https://github.com/Der-Henning/tgtg/actions/workflows/docker-multi-arch.yml/badge.svg?branch=main)](https://github.com/Der-Henning/tgtg/actions/workflows/docker-multi-arch.yml)
[![Tests](https://github.com/Der-Henning/tgtg/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Der-Henning/tgtg/actions/workflows/tests.yml)

# TGTG Scanner

Scans your favorite TGTG Magic Bags for new available items and notifies you via mail, IFTTT, pushSafer or any other WebHook. Notifications will be send when the available amount of Magic Bags rises from zero to something.

Additionally the currently available amounts can be provided via a http server.

Running in a docker container the scanner can be seemlessly integrated with openhab, prometheus and other automation, notification and visualization services.

## Disclaimer

TGTG forbids the use of their plattform the way this tool does. In their Terms and Conditions it says: "The Consumer must not misuse the Platform (including hacking or 'scraping')."

If you use this tool you do it at your own risk. TGTG may stop you from doing so and may even delete your account.

The software is provided as is without warranty of any kind. If you have problems, find bugs or have suggestions for improvement feel free to create an issue or contribute to the project.

## Installation

You can install this tool on any computer. For 24/7 notifications I recommended to install the tool on a NAS like Synology or a Raspberry Pi. You can also use a virtual cloud server. Starting at 1,00 €/Month at Strato.de or try AWS free tier.

If you have any problems or questions feel free to create an issue.

You have the following three options to install the scanner, ascending in complexity:

### Use prebuild Release

This is the simplest but least flexible solution suitable for most operating systems.

1. Download latest [Releases](https://github.com/Der-Henning/tgtg/releases) for your OS
2. Unzip Archiv
3. Edit ```config.ini``` as described in the file
4. Run scanner

You can run the scanner manually if you need it, add it to your autostart or create a service.

### Run with Docker

My prefered method for servers using the pre build multi-arch linux images.

1. Install Docker and docker-compose
2. Edit ```docker-compose.yml``` as described in the file
3. Run ```docker-compose up -d```

### Run from source

Method for developers.

1. Install python and pip
2. Run ```pip install -r requirements.txt```
3. Create ```src/config.ini``` as described in the file ```config.template.ini```
4. Run ```python src/scanner.py```

### Running

When the scanner is started it will first try to login to yout TGTG account. Similar to loging in to the TGTG app, you have to click on the link send to you by mail. This won't work on your mobile phone if you have installed the TGTG app.

After a successfull login the scanner will send a test notification on all configured notifiers. If you don't reveive any notifications, please check your configuration.

### Metrics

Enabling the metrics option will expose a http server on the specified port supplying the currently available items. You can scrape the data with prometheus to create and visualize historic data or use it with your home automation.

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

## Developing

For developement I recommend using docker. The Makefile depends on docker and docker-compose.

Create ```.env``` based on ```sample.env``` for configuration.

```make start-dev``` builds and starts the developement docker image

```make image``` builds docker image

```make bash``` starts python docker image with mounted project

```make builder``` runs pyinstaller in python docker image

```make test``` runs unittests

### Building executables

The executables are build with pyinstaller.

```pip install -r requirements.dev.txt```

```pyinstaller scanner.spec```

### Creating notifiers

Feel free to create and contribute new notifiers for other services and endpoints.

---

<a href="https://www.buymeacoffee.com/henning" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="200"></a>
