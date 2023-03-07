import logging

import requests
from requests.auth import HTTPBasicAuth

from models import Config, Item
from models.errors import MaskConfigurationError, NtfyConfigurationError
from notifiers import Notifier

log = logging.getLogger('tgtg')


class Ntfy(Notifier):
    """Notifier for ntfy"""

    def __init__(self, config: Config):
        self.enabled = config.ntfy.get("enabled", False)
        self.server = config.ntfy.get("server", "https://ntfy.sh")
        self.topic = config.ntfy.get("topic")
        self.title = config.ntfy.get("title", "tgtg")
        self.body = config.ntfy.get("body")
        self.priority = config.ntfy.get("priority", "default")
        self.tags = config.ntfy.get("tags", "tgtg")
        self.username = config.ntfy.get("username")
        self.password = config.ntfy.get("password")
        self.timeout = config.ntfy.get("timeout", 60)
        self.cron = config.ntfy.get("cron")
        self.auth: HTTPBasicAuth = None
        if self.enabled:
            if not self.server or not self.topic:
                raise NtfyConfigurationError()

            self.url = f"{self.server}/{self.topic}"
            log.debug("ntfy url: %s", self.url)

            if (self.username and self.password) is not None:
                self.auth = HTTPBasicAuth(self.username, self.password)
                log.debug("Using basic auth with user '%s' for ntfy",
                          self.username)
            else:
                log.debug("Username or Password missing for ntfy "
                          "authentication, defaulting to no auth")
            try:
                Item.check_mask(self.title)
                Item.check_mask(self.body)
                Item.check_mask(self.tags)
            except MaskConfigurationError as exc:
                raise NtfyConfigurationError(exc.message) from exc

    def send(self, item: Item) -> None:
        """Sends item information via configured ntfy endpoint"""
        if self.enabled and self.cron.is_now:

            log.debug("Sending ntfy Notification")

            title = item.unmask(self.title)
            title = title.encode("utf-8")

            body = item.unmask(self.body)
            body = body.encode("utf-8")

            tags = item.unmask(self.tags)
            tags = tags.encode("utf-8")

            log.debug("ntfy body: %s", body)
            headers = {
                "X-Title": title,
                "X-Message": body,
                "X-Priority": self.priority,
                "X-Tags": tags,
            }
            log.debug("ntfy headers: %s", headers)
            res = requests.post(self.url, headers=headers,
                                timeout=self.timeout, auth=self.auth)
            if not res.ok:
                log.error("ntfy Request failed with status code %s",
                          res.status_code)
                log.debug("Response content: %s", res.text)

    def __repr__(self) -> str:
        return f"ntfy: {self.server}/{self.topic}"
