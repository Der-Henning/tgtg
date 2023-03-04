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
        self.enabled = config.apprise.get("enabled", False)
        self.body = config.apprise.get("body")
        self.url = config.apprise.get("url")
        self.timeout = config.apprise.get("timeout", 60)
        self.cron = config.apprise.get("cron")
        if self.enabled and not self.url:
            raise AppriseConfigurationError()
        if self.enabled:
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
                apobj = apprise.Apprise()
                apobj.add(self.url)
                apobj.notify(
                    body=body
                )
                apobj.clear()

    def __repr__(self) -> str:
        return f"Apprise {self.url}"
