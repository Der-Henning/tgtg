import json
import logging

import requests

from models import Config, Item
from models.errors import MaskConfigurationError, NtfyConfigurationError
from notifiers.webhook import WebHook

log = logging.getLogger('tgtg')


class Ntfy(WebHook):
    """Notifier for ntfy"""

    def __init__(self, config: Config):
        self.enabled = config.ntfy.get("enabled", False)
        self.server = config.ntfy.get("server", "https://ntfy.sh")
        self.topic = config.ntfy.get("topic")
        self.title = config.ntfy.get("title", "tgtg")
        self.message = config.ntfy.get("message")
        self.priority = config.ntfy.get("priority", "default")
        self.tags = config.ntfy.get("tags", "tgtg")
        self.username = config.ntfy.get("username")
        self.password = config.ntfy.get("password")
        self.timeout = config.ntfy.get("timeout", 60)
        self.cron = config.ntfy.get("cron")

        self.headers = None
        self.auth = None
        self.body = None
        self.method = "POST"
        self.type = None

        if self.enabled:
            if not self.server or not self.topic:
                raise NtfyConfigurationError()

            self.url = f"{self.server}/{self.topic}"
            log.debug("ntfy url: %s", self.url)

            if (self.username and self.password) is not None:
                self.auth = requests.auth.HTTPBasicAuth(self.username, self.password)
                log.debug("Using basic auth with user '%s' for ntfy", self.username)
            elif (self.username or self.password) is not None:
                log.warning("Username or Password missing for ntfy authentication, defaulting to no auth")

            try:
                Item.check_mask(self.title)
                Item.check_mask(self.message)
                Item.check_mask(self.tags)
            except MaskConfigurationError as exc:
                raise NtfyConfigurationError(exc.message) from exc

    def send(self, item: Item) -> None:
        """Sends item information via configured ntfy endpoint"""
        if self.enabled and self.cron.is_now:

            log.debug("Sending ntfy Notification")

            title = item.unmask(self.title)
            title = title.encode("utf-8")

            message = item.unmask(self.message)
            message = message.encode("utf-8")

            tags = item.unmask(self.tags)
            tags = tags.encode("utf-8")

            self.headers = {
                "X-Title": title,
                "X-Message": message,
                "X-Priority": self.priority,
                "X-Tags": tags,
            }

            WebHook.send(self, item)

    def __repr__(self) -> str:
        return f"ntfy: {self.server}/{self.topic}"
