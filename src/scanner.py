import logging
import sys
from random import random
from time import sleep
from typing import List, NoReturn

from models import Config, Item, Metrics
from notifiers import Notifiers
from tgtg import TgtgClient

log = logging.getLogger("tgtg")


class Scanner:
    def __init__(self, config: Config):
        self.config = config
        self.metrics = Metrics(self.config.metrics_port)
        self.item_ids = self.config.item_ids
        self.cron = self.config.schedule_cron
        self.amounts = {}
        self.notifiers = None
        self.tgtg_client = TgtgClient(
            email=self.config.tgtg.get("username"),
            timeout=self.config.tgtg.get("timeout"),
            access_token_lifetime=self.config.tgtg.get(
                "access_token_lifetime"),
            max_polling_tries=self.config.tgtg.get("max_polling_tries"),
            polling_wait_time=self.config.tgtg.get("polling_wait_time"),
            access_token=self.config.tgtg.get("access_token"),
            refresh_token=self.config.tgtg.get("refresh_token"),
            user_id=self.config.tgtg.get("user_id"),
        )

    def _get_test_item(self) -> Item:
        """
        Returns an item for test notifications
        """
        items = sorted(self._get_favorites(),
                       key=lambda x: x.items_available,
                       reverse=True)
        if items:
            return items[0]
        items = sorted(
            [
                Item(item)
                for item in self.tgtg_client.get_items(
                    favorites_only=False,
                    latitude=53.5511,
                    longitude=9.9937,
                    radius=50)
            ],
            key=lambda x: x.items_available,
            reverse=True,
        )
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
                log.error("itemID %s Error! - %s", item_id, sys.exc_info())
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
            self.tgtg_client.user_id,
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
                    favorites_only=True, page_size=page_size, page=page
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
        Checks if the available item amount raised from zero to something
        and triggers notifications.
        """
        try:
            if (
                self.amounts[item.item_id] == 0
                and item.items_available > self.amounts[item.item_id]
            ):
                self._send_messages(item)
                self.metrics.send_notifications.labels(
                    item.item_id, item.display_name
                ).inc()
            self.metrics.item_count.labels(item.item_id,
                                           item.display_name
                                           ).set(item.items_available)
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
        log.info(
            "Sending notifications for %s - %s bags available",
            item.display_name,
            item.items_available,
        )
        self.notifiers.send(item)

    def run(self) -> NoReturn:
        """
        Main Loop of the Scanner
        """
        # activate and test notifiers
        if self.config.metrics:
            self.metrics.enable_metrics()
        self.notifiers = Notifiers(self.config)
        if not self.config.disable_tests and \
                self.notifiers.notifier_count > 0:
            log.info("Sending test Notifications ...")
            self.notifiers.send(self._get_test_item())
        # test tgtg API
        self.tgtg_client.login()
        self.config.save_tokens(
            self.tgtg_client.access_token,
            self.tgtg_client.refresh_token,
            self.tgtg_client.user_id,
        )
        # start scanner
        log.info("Scanner started ...")
        running = True
        if self.cron.cron != "* * * * *":
            log.info("Active on schedule: %s", self.cron.description)
        while True:
            if self.cron.is_now:
                if not running:
                    log.info("Scanner reenabled by cron schedule.")
                    running = True
                try:
                    self._job()
                except Exception:
                    log.error("Job Error! - %s", sys.exc_info())
            elif running:
                log.info("Scanner disabled by cron schedule.")
                running = False
            sleep(self.config.sleep_time * (0.9 + 0.2 * random()))

    def __del__(self) -> None:
        """
        Cleanup on shutdown
        """
        if self.notifiers:
            self.notifiers.stop()

    def get_credentials(self) -> dict:
        """Returns current tgtg credentials.

        Returns:
            dict: dictionary containing access token, refresh token and user id
        """
        return self.tgtg_client.get_credentials()

    def get_items(self, lat, lng, radius) -> List[dict]:
        """Get items by geographic position.

        Args:
            lat (float): latitude
            lng (float): longitude
            radius (int): radius in meter

        Returns:
            List: List of found items
        """
        return self.tgtg_client.get_items(
            favorites_only=False,
            latitude=lat,
            longitude=lng,
            radius=radius,
        )

    def get_favorites(self) -> List[dict]:
        """Returns favorites of the current tgtg account

        Returns:
            List: List of items
        """
        items = []
        page = 1
        page_size = 100
        while True:
            new_items = self.tgtg_client.get_items(
                favorites_only=True,
                page_size=page_size,
                page=page
            )
            items += new_items
            if len(new_items) < page_size:
                break
            page += 1
        return items

    def set_favorite(self, item_id: str) -> None:
        """Add item to favorites.

        Args:
            item_id (str): Item ID
        """
        self.tgtg_client.set_favorite(item_id=item_id, is_favorite=True)

    def unset_favorite(self, item_id: str) -> None:
        """Remove item from favorites.

        Args:
            item_id (str): Item ID
        """
        self.tgtg_client.set_favorite(item_id=item_id, is_favorite=False)

    def unset_all_favorites(self) -> None:
        """Remove all items from favorites."""
        item_ids = [item.get("item", {}).get("item_id")
                    for item in self.get_favorites()]
        for item_id in item_ids:
            self.unset_favorite(item_id)


if __name__ == "__main__":
    print("Please use main.py.")
