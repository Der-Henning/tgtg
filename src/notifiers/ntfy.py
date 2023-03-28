import logging

from requests.auth import HTTPBasicAuth

from models import Config, Item
from models.errors import MaskConfigurationError, NtfyConfigurationError
from notifiers.webhook import WebHook

log = logging.getLogger('tgtg')


class Ntfy(WebHook):
    """Notifier for Ntfy"""

    def __init__(self, config: Config):
        self.enabled = config.ntfy.get("enabled", False)
        self.server = config.ntfy.get("server", "https://ntfy.sh")
        self.topic = config.ntfy.get("topic")
        self.title = config.ntfy.get("title", "tgtg")
        self.message = config.ntfy.get("message")
        self.body = config.ntfy.get("body")
        self.priority = config.ntfy.get("priority", "default")
        self.tags = config.ntfy.get("tags", "tgtg")
        self.click = config.ntfy.get("click")
        self.username = config.ntfy.get("username")
        self.password = config.ntfy.get("password")
        self.timeout = config.ntfy.get("timeout", 60)
        self.cron = config.ntfy.get("cron")
        self.headers = None
        self.auth = None
        self.method = "POST"
        self.type = None

        if self.enabled:
            if not self.server or not self.topic:
                raise NtfyConfigurationError()
            self.url = f"{self.server}/{self.topic}"
            log.debug("Ntfy url: %s", self.url)
            if (self.username and self.password) is not None:
                self.auth = HTTPBasicAuth(self.username, self.password)
                log.debug("Using basic auth with user '%s' for Ntfy",
                          self.username)
            elif (self.username or self.password) is not None:
                log.warning("Username or Password missing for Ntfy "
                            "authentication, defaulting to no auth")
            try:
                Item.check_mask(self.title)
                Item.check_mask(self.message)
                Item.check_mask(self.tags)
                Item.check_mask(self.click)
            except MaskConfigurationError as exc:
                raise NtfyConfigurationError(exc.message) from exc

    def _send(self, item: Item) -> None:
        """Sends item information via configured Ntfy endpoint"""
        title = item.unmask(self.title).encode("utf-8")
        message = item.unmask(self.message).encode("utf-8")
        tags = item.unmask(self.tags).encode("utf-8")
        click = item.unmask(self.click).encode("utf-8")
        self.headers = {
            "X-Title": title,
            "X-Message": message,
            "X-Priority": self.priority,
            "X-Tags": tags,
            "X-Click": click
        }
        super()._send(item)

    def __repr__(self) -> str:
        return f"Ntfy: {self.server}/{self.topic}"
