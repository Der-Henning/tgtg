import sys
import logging
from time import sleep
from os import path
from random import random
from packaging import version
import requests

from models import Item, Config, Metrics, TgtgAPIError, Error, ConfigurationError, TGTGConfigurationError
from notifiers import Notifiers
from tgtg import TgtgClient

VERSION_URL = 'https://api.github.com/repos/Der-Henning/tgtg/releases/latest'
VERSION = "1.8.0"

prog_folder = path.dirname(sys.executable) if getattr(
    sys, '_MEIPASS', False) else path.dirname(path.abspath(__file__))
config_file = path.join(prog_folder, 'config.ini')
log_file = path.join(prog_folder, 'scanner.log')
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, mode="w"),
        logging.StreamHandler()
    ])
log = logging.getLogger('tgtg')


class Scanner():
    def __init__(self):
        self.config = Config(config_file) if path.isfile(
            config_file) else Config()
        if self.config.debug:
            # pylint: disable=E1103
            loggers = [logging.getLogger(name)
                       for name in logging.root.manager.loggerDict]
            # pylint: enable=E1103
            for logger in loggers:
                logger.setLevel(logging.DEBUG)
            log.info("Debugging mode enabled")
        self.metrics = Metrics()
        if self.config.metrics:
            self.metrics.enable_metrics()
        self.item_ids = self.config.item_ids
        self.amounts = {}
        try:
            self.tgtg_client = TgtgClient(
                email=self.config.tgtg["username"],
                timeout=self.config.tgtg["timeout"],
                access_token_lifetime=self.config.tgtg["access_token_lifetime"],
                max_polling_tries=self.config.tgtg["max_polling_tries"],
                polling_wait_time=self.config.tgtg["polling_wait_time"],
                access_token=self.config.tgtg["access_token"],
                refresh_token=self.config.tgtg["refresh_token"],
                user_id=self.config.tgtg["user_id"]
            )
            self.tgtg_client.login()
        except TgtgAPIError as err:
            raise
        except Error as err:
            log.error(err)
            raise TGTGConfigurationError() from err
        self.notifiers = Notifiers(self.config)

    def _job(self):
        for item_id in self.item_ids:
            try:
                if item_id != "":
                    data = self.tgtg_client.get_item(item_id)
                    self._check_item(Item(data))
            except Exception:
                log.error(
                    "itemID %s Error! - %s", item_id, sys.exc_info())
        for data in self._get_favorites():
            try:
                self._check_item(Item(data))
            except Exception:
                log.error("check item error! - %s", sys.exc_info())
        log.debug("new State: %s", self.amounts)
        self.config.save_tokens(
            self.tgtg_client.access_token, 
            self.tgtg_client.refresh_token,
            self.tgtg_client.user_id
        )

    def _get_favorites(self):
        items = []
        page = 1
        page_size = 100
        error_count = 0
        while True and error_count < 5:
            try:
                new_items = self.tgtg_client.get_items(
                    favorites_only=True,
                    page_size=page_size,
                    page=page
                )
                items += new_items
                if len(new_items) < page_size:
                    break
                page += 1
            except Exception:
                log.error("get item error! - %s", sys.exc_info())
                error_count += 1
                self.metrics.get_favorites_errors.inc()
        return items

    def _check_item(self, item: Item):
        try:
            if self.amounts[item.item_id] == 0 and item.items_available > self.amounts[item.item_id]:
                self._send_messages(item)
                self.metrics.send_notifications.labels(
                    item.item_id, item.display_name).inc()
            self.metrics.item_count.labels(
                item.item_id, item.display_name).set(item.items_available)
        except Exception:
            self.amounts[item.item_id] = item.items_available
        finally:
            if self.amounts[item.item_id] != item.items_available:
                log.info("%s - new amount: %s",
                         item.display_name, item.items_available)
                self.amounts[item.item_id] = item.items_available

    def _send_messages(self, item: Item):
        log.info("Sending notifications for %s - %s bags available",
                 item.display_name, item.items_available)
        self.notifiers.send(item)

    def run(self):
        log.info("Scanner started ...")
        while True:
            try:
                self._job()
            except Exception:
                log.error("Job Error! - %s", sys.exc_info())
            finally:
                sleep(self.config.sleep_time * (0.9 + 0.2 * random()))


def welcome_message():
    # pylint: disable=W1401
    log.info("  ____  ___  ____  ___    ____   ___   __   __ _  __ _  ____  ____  ")
    log.info(" (_  _)/ __)(_  _)/ __)  / ___) / __) / _\ (  ( \(  ( \(  __)(  _ \ ")
    log.info("   )( ( (_ \  )( ( (_ \  \___ \( (__ /    \/    //    / ) _)  )   / ")
    log.info("  (__) \___/ (__) \___/  (____/ \___)\_/\_/\_)__)\_)__)(____)(__\_) ")
    log.info("")
    log.info("Version %s", VERSION)
    log.info("©2021, Henning Merklinger")
    log.info("For documentation and support please visit https://github.com/Der-Henning/tgtg")
    log.info("")
    # pylint: enable=W1401


def check_version():
    try:
        last_release = requests.get(VERSION_URL).json()
        if version.parse(VERSION) < version.parse(last_release['tag_name']):
            log.info("New Version %s available!",
                     version.parse(last_release['tag_name']))
            log.info("Please visit %s", last_release['html_url'])
            log.info("")
    except Exception:
        log.error("Version check Error! - %s", sys.exc_info())


def main():
    try:
        welcome_message()
        check_version()
        scanner = Scanner()
        scanner.run()
    except ConfigurationError as err:
        log.error("Configuration Error - %s", err)
        sys.exit(1)
    except TgtgAPIError as err:
        log.error("TGTG API Error: %s", err)
        sys.exit(1)
    except KeyboardInterrupt:
        log.info("Shutting down scanner ...")
    except SystemExit:
        sys.exit(1)
    except:
        log.error("Unexpected Error! - %s", sys.exc_info())
        sys.exit(1)


if __name__ == "__main__":
    main()
