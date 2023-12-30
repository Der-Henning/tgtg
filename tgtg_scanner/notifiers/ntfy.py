import logging
from typing import Union

from requests.auth import HTTPBasicAuth

from tgtg_scanner.errors import MaskConfigurationError, NtfyConfigurationError
from tgtg_scanner.models import Config, Favorites, Item, Reservations
from tgtg_scanner.models.reservations import Reservation
from tgtg_scanner.notifiers.webhook import WebHook

log = logging.getLogger("tgtg")


class Ntfy(WebHook):
    """Notifier for Ntfy"""

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        super(WebHook, self).__init__(config, reservations, favorites)
        self.enabled = config.ntfy.enabled
        self.server = config.ntfy.server
        self.topic = config.ntfy.topic
        self.title = config.ntfy.title
        self.message = config.ntfy.message
        self.body = config.ntfy.body
        self.priority = config.ntfy.priority
        self.tags = config.ntfy.tags
        self.click = config.ntfy.click
        self.username = config.ntfy.username
        self.password = config.ntfy.password
        self.timeout = config.ntfy.timeout
        self.cron = config.ntfy.cron
        self.headers = dict()
        self.auth = None
        self.method = "POST"
        self.type = None

        if self.enabled:
            if not self.server or not self.topic:
                raise NtfyConfigurationError()
            self.url = f"{self.server}/{self.topic}"
            log.debug("Ntfy url: %s", self.url)
            if self.username is not None and self.password is not None:
                self.auth = HTTPBasicAuth(self.username, self.password)
                log.debug("Using basic auth with user '%s' for Ntfy", self.username)
            elif (self.username or self.password) is not None:
                log.warning("Username or Password missing for Ntfy authentication, defaulting to no auth")
            try:
                Item.check_mask(self.title)
                Item.check_mask(self.message)
                Item.check_mask(self.tags)
                Item.check_mask(self.click)
            except MaskConfigurationError as exc:
                raise NtfyConfigurationError(exc.message) from exc

    def _send(self, item: Union[Item, Reservation]) -> None:
        """Sends item information via configured Ntfy endpoint"""
        if isinstance(item, Item):
            title = item.unmask(self.title).encode("utf-8")
            message = item.unmask(self.message).encode("utf-8")
            tags = item.unmask(self.tags).encode("utf-8")
            click = item.unmask(self.click).encode("utf-8")
            self.headers = {
                "X-Title": title,
                "X-Message": message,
                "X-Priority": self.priority,
                "X-Tags": tags,
                "X-Click": click,
            }
            super()._send(item)

    def __repr__(self) -> str:
        return f"Ntfy: {self.server}/{self.topic}"
