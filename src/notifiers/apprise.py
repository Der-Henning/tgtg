import logging

import apprise

from models import Config, Item
from models.errors import AppriseConfigurationError, MaskConfigurationError
from notifiers import Notifier

log = logging.getLogger('tgtg')


class Apprise(Notifier):
    """
    Notifier for Apprise. \n
    For more information on Apprise visit\n
    https://github.com/caronc/apprise
    """

    def __init__(self, config: Config):
        self.instance = None
        self.enabled = config.apprise.get("enabled", False)
        self.body = config.apprise.get("body")
        self.url = config.apprise.get("url")
        self.timeout = config.apprise.get("timeout", 60)
        self.cron = config.apprise.get("cron")
        if self.enabled and (not self.url or not self.body):
            raise AppriseConfigurationError()
        if self.enabled:
            self.instance = apprise.Apprise()
            self.instance.add(self.url)
            try:
                Item.check_mask(self.body)
                Item.check_mask(self.url)
            except MaskConfigurationError as exc:
                raise AppriseConfigurationError(exc.message) from exc

    def send(self, item: Item) -> None:
        """Sends item information via configured Apprise URL"""
        if self.enabled and self.cron.is_now:
            log.debug("Sending Apprise Notification")
            url = item.unmask(self.url)
            log.debug("Apprise url: %s", url)
            if self.body:
                body = item.unmask(self.body)
                self.instance.notify(
                    body=body
                )

    def stop(self):
        if self.instance is not None:
            self.instance.clear()

    def __repr__(self) -> str:
        return f"Apprise {self.url}"
