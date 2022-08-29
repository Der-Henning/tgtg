import sys
import logging
from time import sleep
from os import path
from random import random
from typing import NoReturn
from packaging import version
import requests
import pycron
from cron_descriptor import get_description

from models import Item, Config, Metrics
from models.errors import TgtgAPIError, Error, ConfigurationError, TGTGConfigurationError
from notifiers import Notifiers
from tgtg import TgtgClient

VERSION_URL = 'https://api.github.com/repos/Der-Henning/tgtg/releases/latest'
VERSION = "1.11.5"

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
    def __init__(self, notifiers: bool = True):
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
            self.config.save_tokens(
                self.tgtg_client.access_token,
                self.tgtg_client.refresh_token,
                self.tgtg_client.user_id
            )
        except TgtgAPIError as err:
            raise err
        except Error as err:
            log.error(err)
            raise TGTGConfigurationError() from err
        if notifiers:
            if self.config.metrics:
                self.metrics.enable_metrics()
            self.notifiers = Notifiers(self.config)
            if not self.config.disable_tests:
                log.info("Sending test Notifications ...")
                self.notifiers.send(self._test_item)

    @property
    def _test_item(self) -> Item:
        """
        Returns an item for test notifications
        """
        items = sorted(self._get_favorites(), key=lambda x: x.items_available, reverse=True)
        if items:
            return items[0]
        items = sorted([Item(item) for item in self.tgtg_client.get_items(
            favorites_only=False, latitude=53.5511, longitude=9.9937, radius=50
        )], key=lambda x: x.items_available, reverse=True)
        return items[0]

    def _job(self) -> None:
        """
        Job iterates over all monitored items
        """
        for item_id in self.item_ids:
            try:
                if item_id != "":
                    item = Item(self.tgtg_client.get_item(item_id))
                    self._check_item(item)
            except Exception:
                log.error(
                    "itemID %s Error! - %s", item_id, sys.exc_info())
        for item in self._get_favorites():
            try:
                self._check_item(item)
            except Exception:
                log.error("check item error! - %s", sys.exc_info())
        log.debug("new State: %s", self.amounts)
        if len(self.amounts) == 0:
            log.warning("No items in observation! Did you add any favorites?")
        self.config.save_tokens(
            self.tgtg_client.access_token,
            self.tgtg_client.refresh_token,
            self.tgtg_client.user_id
        )

    def _get_favorites(self) -> list[Item]:
        """
        Get favorites as list of Items
        """
        items = []
        page = 1
        page_size = 100
        error_count = 0
        while error_count < 5:
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
        return [Item(item) for item in items]

    def _check_item(self, item: Item) -> None:
        """
        Checks if the available item amount raised from zero to something and triggers notifications.
        """
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

    def _send_messages(self, item: Item) -> None:
        """
        Send notifications for Item
        """
        log.info("Sending notifications for %s - %s bags available",
                 item.display_name, item.items_available)
        self.notifiers.send(item)

    def run(self) -> NoReturn:
        """
        Main Loop of the Scanner
        """
        log.info("Scanner started ...")
        if (self.config.schedule_cron != '* * * * *'):
            try:
                log.info("Schedule cron expression: " + get_description(self.config.schedule_cron))
            except Exception:
                log.warning("Schedule cron expression parsing error - %s", sys.exc_info())
                log.info("Schedule cron expression is ignored")
                self.config.schedule_cron = '* * * * *'
        while True:
            if (pycron.is_now(self.config.schedule_cron)):
                try:
                    self._job()
                    if self.tgtg_client.captcha_error_count > 10:
                        log.warning("Too many 403 Errors. Sleeping for 1 hour.")
                        sleep(60 * 60)
                        log.info("Continuing scanning.")
                        self.tgtg_client.captcha_error_count = 0
                except Exception:
                    log.error("Job Error! - %s", sys.exc_info())
            sleep(self.config.sleep_time * (0.9 + 0.2 * random()))

    def __del__(self) -> None:
        """
        Cleanup on shutdown
        """
        try:
            if hasattr(self, 'notifiers') and self.notifiers.telegram.updater:
                self.notifiers.telegram.updater.stop()
        except Exception as exc:
            log.warning(exc)


def welcome_message() -> None:
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


def check_version() -> None:
    try:
        res = requests.get(VERSION_URL)
        res.raise_for_status()
        lastest_release=res.json()
        if version.parse(VERSION) < version.parse(lastest_release['tag_name']):
            log.info("New Version %s available!",
                     version.parse(lastest_release['tag_name']))
            log.info("Please visit %s", lastest_release['html_url'])
            log.info("")
    except (requests.exceptions.RequestException, version.InvalidVersion, ValueError) as err:
        log.error("Failed checking for new Version! - %s", err)


def main() -> NoReturn:
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


if __name__ == "__main__":
    main()
