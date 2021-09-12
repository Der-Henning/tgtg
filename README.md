# TGTG Scanner

Scanns favorite TGTG Magic Bags for new available items and notifies via mail, ifttt or pushsafer.

## Disclaimer

TGTG forbids the use of their plattform the way this tool does. In their Terms and Conditions it says: "The Consumer must not misuse the Platform (including hacking or 'scraping')."

If you use this tool you do it at your own risk. TGTG may stop you from doing so and may even delete your account.

## Installation

You can install this tool on any computer.
It is recommended to install the tool on a NAS like Synology or a Raspberry Pi. You can also use a virtual cloud server. Starting at 1,00 €/Month at Strato.de or try AWS free tier.

Because of the hugh range of possibilities I cannot give an indepth guide for all of them. First of all I will only give a rough overview. Google is your friend. 

If someone wants to make a detailed guide, feel free to contribute to the project.

### Use prebuild Release

1. Download Release from https://github.com/Der-Henning/tgtg/releases
2. Unzip Archiv
3. Create ```config.ini``` as described in the file ```config.template.ini```
4. Run scanner

### Install from source

#### Install as a service

1. Install python3
2. Run ```pip3 install -r requirements.txt```
3. Create ```/src/config.ini``` as described in the file ```config.template.ini```
4. Register ```python {install directory}/src/scanner.py``` as a service or just run it manually

#### With Docker

1. Install Docker and docker-compose
2. Edit ```docker-compose.yml``` as described in the file
3. Run ```docker-compose up -d```

### Running

When the scanner is started it will send a test notification on all configured notifiers. If you don't reveive any notifications, please check your configuration.