import logging
import sys
from random import random
from time import sleep
from typing import NoReturn

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
from tgtg_scanner.models.stock_monitor import StockMonitor
from tgtg_scanner.notifiers import Notifiers
from tgtg_scanner.tgtg_client import BASE_URL, TgtgClient, extract_datadome, normalize_cookie, resolve_user_agent

log = logging.getLogger("tgtg")


class Activity:
    """Activity class that creates a spinner if active is True."""

    def __init__(self, active: bool):
        self.active = active
        self.spinner = None
        if self.active:
            self.spinner = Spinner("Scanning... ")

    def next(self) -> None:
        """Next function that updates the spinner."""
        if self.spinner:
            self.spinner.next()

    def flush(self) -> None:
        """Flush function that flushes the spinner."""
        if self.spinner:
            sys.stdout.write("\x1b[80D\x1b[K")
            sys.stdout.flush()


class Scanner:
    """Main Scanner class."""

    def __init__(self, config: Config):
        self.config = config
        self.metrics = Metrics(self.config.metrics_port)
        self.item_ids = {item_id for item_id in self.config.item_ids if item_id}
        self.cron = self.config.schedule_cron
        self.monitor = StockMonitor(price_monitoring=self.config.price_monitoring)
        self.notifiers: Notifiers | None = None
        self.location: Location | None = None
        self.tgtg_client = self._build_client(config)
        self.reservations = Reservations(self.tgtg_client)
        self.favorites = Favorites(self.tgtg_client)

    @staticmethod
    def _build_client(config: Config) -> TgtgClient:
        tgtg = config.tgtg
        kwargs = {
            "url": tgtg.base_url or BASE_URL,
            "email": tgtg.username,
            "access_token": tgtg.access_token,
            "refresh_token": tgtg.refresh_token,
            "cookie": normalize_cookie(tgtg.datadome),
            "timeout": tgtg.timeout,
            "access_token_lifetime": tgtg.access_token_lifetime,
            "pin_port": config.port,
            "max_polling_tries": tgtg.max_polling_tries,
            "polling_wait_time": tgtg.polling_wait_time,
        }
        user_agent = resolve_user_agent(tgtg.user_agent, tgtg.apk_version)
        if user_agent:
            kwargs["user_agent"] = user_agent
        return TgtgClient(**kwargs)

    @property
    def state(self) -> dict[str, Item]:
        """Current item state from the stock monitor."""
        return self.monitor.state

    def _item_from_api(self, data: dict) -> Item:
        return Item(data, self.location, self.config.locale, self.config.time_format)

    def _save_tokens(self) -> None:
        self.config.save_tokens(
            self.tgtg_client.access_token or "",
            self.tgtg_client.refresh_token or "",
            extract_datadome(self.tgtg_client),
        )

    def _get_test_item(self) -> Item:
        """Returns an item for test notifications."""
        items = sorted(self._load_favorite_items(), key=lambda x: x.items_available, reverse=True)
        if items:
            return items[0]
        items = sorted(
            [
                self._item_from_api(item)
                for item in self.tgtg_client.get_items(
                    favorites_only=False,
                    latitude=53.5511,
                    longitude=9.9937,
                    radius=50,
                )
            ],
            key=lambda x: x.items_available,
            reverse=True,
        )
        return items[0]

    def _load_items(self) -> list[Item]:
        """Fetch configured item IDs and account favorites as Items."""
        items: list[Item] = []
        for item_id in self.item_ids:
            try:
                items.append(self._item_from_api(self.tgtg_client.get_item(item_id)))
            except TgtgAPIError as err:
                log.error(err)
        items.extend(self._load_favorite_items())
        return items

    def _load_favorite_items(self) -> list[Item]:
        try:
            return [self._item_from_api(item) for item in self.tgtg_client.get_favorites()]
        except TgtgAPIError as err:
            log.error(err)
            self.metrics.get_favorites_errors.inc()
            return []

    def _job(self) -> None:
        """Job iterates over all monitored items."""
        if self.notifiers is None:
            raise RuntimeError("Notifiers not initialized!")

        for item in self._load_items():
            if self.monitor.observe(item):
                self._send_messages(item)
                self.metrics.send_notifications.labels(item.item_id, item.display_name).inc()
            self.metrics.update(item)

        amounts = {item_id: item.items_available for item_id, item in self.monitor.state.items()}
        log.debug("new State: %s", amounts)
        self.reservations.make_orders(self.monitor.state, self.notifiers.send)

        if not self.monitor.state:
            log.warning("No items in observation! Did you add any favorites?")

        self._save_tokens()

    def _send_messages(self, item: Item) -> None:
        """Send notifications for Item."""
        if self.notifiers is None:
            raise RuntimeError("Notifiers not initialized!")

        log.info(
            "Sending notifications for %s - %s bags available",
            item.display_name,
            item.items_available,
        )
        self.notifiers.send(item)

    def run(self) -> NoReturn:
        """Main Loop of the Scanner."""
        # test tgtg API
        self.tgtg_client.login()
        self._save_tokens()
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
                    steps = max(int(sleep_time), 1)
                    for _ in range(steps):
                        activity.next()
                        sleep(sleep_time / steps)
                        activity.flush()
            elif running:
                log.info("Scanner disabled by cron schedule.")
                running = False
            else:
                sleep(60)

    def stop(self) -> None:
        """Stop scanner."""
        if self.notifiers:
            self.notifiers.stop()

    def get_credentials(self) -> dict:
        """Returns current tgtg credentials.

        Returns:
            dict: dictionary containing access token, refresh token and datadome cookie

        """
        return self.tgtg_client.get_credentials()

    def get_items(self, lat, lng, radius) -> list[dict]:
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

    def get_favorites(self) -> list[dict]:
        """Returns favorites of the current tgtg account.

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
            if item_id:
                self.unset_favorite(item_id)


if __name__ == "__main__":
    print("Please use __main__.py.")
