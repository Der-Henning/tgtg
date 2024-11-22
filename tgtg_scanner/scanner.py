import logging
import sys
from random import random
from time import sleep
from typing import Dict, List, NoReturn, Union

from progress.spinner import Spinner

from tgtg_scanner.errors import TgtgAPIError
from tgtg_scanner.models import (
    Config,
    Cron,
    Favorites,
    Item,
    Location,
    Metrics,
    Reservations,
)
from tgtg_scanner.notifiers import Notifiers
from tgtg_scanner.tgtg import TgtgClient

log = logging.getLogger("tgtg")


class Activity:
    """Activity class that creates a spinner if active is True"""

    def __init__(self, active: bool):
        self.active = active
        self.spinner = None
        if self.active:
            self.spinner = Spinner("Scanning... ")

    def next(self) -> None:
        """Next function that updates the spinner"""
        if self.spinner:
            self.spinner.next()

    def flush(self) -> None:
        """Flush function that flushes the spinner"""
        if self.spinner:
            sys.stdout.write("\x1b[80D\x1b[K")
            sys.stdout.flush()


class Scanner:
    """Main Scanner class"""

    def __init__(self, config: Config):
        self.config = config
        self.metrics = Metrics(self.config.metrics_port)
        self.item_ids = set(self.config.item_ids)
        self.cron = self.config.schedule_cron
        self.state: Dict[str, Item] = {}
        self.notifiers: Union[Notifiers, None] = None
        self.location: Union[Location, None] = None
        self.tgtg_client = TgtgClient(
            email=self.config.tgtg.username,
            timeout=self.config.tgtg.timeout,
            access_token_lifetime=self.config.tgtg.access_token_lifetime,
            max_polling_tries=self.config.tgtg.max_polling_tries,
            polling_wait_time=self.config.tgtg.polling_wait_time,
            access_token=self.config.tgtg.access_token,
            refresh_token=self.config.tgtg.refresh_token,
            datadome_cookie=self.config.tgtg.datadome,
            base_url=self.config.tgtg.base_url,
        )
        self.reservations = Reservations(self.tgtg_client)
        self.favorites = Favorites(self.tgtg_client)

    def _get_test_item(self) -> Item:
        """
        Returns an item for test notifications
        """
        items = sorted(self._get_favorites(), key=lambda x: x.items_available, reverse=True)

        if items:
            return items[0]
        items = sorted(
            [
                Item(item, self.location, self.config.locale)
                for item in self.tgtg_client.get_items(favorites_only=False, latitude=53.5511, longitude=9.9937, radius=50)
            ],
            key=lambda x: x.items_available,
            reverse=True,
        )

        return items[0]

    def _job(self) -> None:
        """
        Job iterates over all monitored items
        """
        if self.notifiers is None:
            raise RuntimeError("Notifiers not initialized!")

        items: list[Item] = []
        for item_id in self.item_ids:
            try:
                if item_id != "":
                    item_dict = self.tgtg_client.get_item(item_id)
                    items.append(Item(item_dict, self.location, self.config.locale))
            except TgtgAPIError as err:
                log.error(err)
        items += self._get_favorites()
        for item in items:
            self._check_item(item)

        amounts = {item_id: item.items_available for item_id, item in self.state.items() if item is not None}
        log.debug("new State: %s", amounts)
        self.reservations.make_orders(self.state, self.notifiers.send)

        if len(self.state) == 0:
            log.warning("No items in observation! Did you add any favorites?")

        self.config.save_tokens(
            self.tgtg_client.access_token,
            self.tgtg_client.refresh_token,
            self.tgtg_client.datadome_cookie,
        )

    def _get_favorites(self) -> list[Item]:
        """
        Get favorites as list of Items

        Returns:
            List: List of items
        """
        try:
            items = self.get_favorites()
        except TgtgAPIError as err:
            log.error(err)
            return []
        return [Item(item, self.location, self.config.locale) for item in items]

    def _check_item(self, item: Item) -> None:
        """
        Checks if the available item amount raised from zero to something
        and triggers notifications.
        """
        state_item = self.state.get(item.item_id)
        if state_item is not None:
            if state_item.items_available == item.items_available:
                return
            log.info("%s - new amount: %s", item.display_name, item.items_available)
            if state_item.items_available == 0 and item.items_available > 0:
                self._send_messages(item)
                self.metrics.send_notifications.labels(item.item_id, item.display_name).inc()
        self.metrics.update(item)
        self.state[item.item_id] = item

    def _send_messages(self, item: Item) -> None:
        """
        Send notifications for Item
        """
        if self.notifiers is None:
            raise RuntimeError("Notifiers not initialized!")

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
        # test tgtg API
        self.tgtg_client.login()
        self.config.save_tokens(
            self.tgtg_client.access_token,
            self.tgtg_client.refresh_token,
            self.tgtg_client.datadome_cookie,
        )
        # activate location service
        self.location = Location(
            self.config.location.enabled,
            self.config.location.google_maps_api_key,
            self.config.location.origin_address,
        )
        # activate and test notifiers
        if self.config.metrics:
            self.metrics.enable_metrics()
        self.notifiers = Notifiers(self.config, self.reservations, self.favorites)
        self.notifiers.start()
        if not self.config.disable_tests and self.notifiers.notifier_count > 0:
            log.info("Sending test Notifications ...")
            self.notifiers.send(self._get_test_item())
        # start scanner
        log.info("Scanner started ...")
        running = True
        if self.cron != Cron("* * * * *"):
            log.info("Active on schedule: %s", self.cron.get_description(self.config.locale))
        activity = Activity(self.config.activity and not (self.config.docker or self.config.quiet))
        while True:
            if self.cron.is_now:
                if not running:
                    log.info("Scanner reenabled by cron schedule.")
                    running = True
                try:
                    self._job()
                except Exception:
                    log.error("Job Error! - %s", sys.exc_info())
                finally:
                    sleep_time = self.config.sleep_time * (0.9 + 0.2 * random())
                    for _ in range(int(sleep_time)):
                        activity.next()
                        sleep(sleep_time / int(sleep_time))
                        activity.flush()
            elif running:
                log.info("Scanner disabled by cron schedule.")
                running = False
            else:
                sleep(60)

    def stop(self) -> None:
        """
        Stop scanner.
        """
        if self.notifiers:
            self.notifiers.stop()

    def get_credentials(self) -> dict:
        """Returns current tgtg credentials.

        Returns:
            dict: dictionary containing access token, refresh token,
                  user id and datadome cookie
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
        return self.tgtg_client.get_favorites()

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
        item_ids = [item.get("item", {}).get("item_id") for item in self.get_favorites()]
        for item_id in item_ids:
            self.unset_favorite(item_id)


if __name__ == "__main__":
    print("Please use __main__.py.")
