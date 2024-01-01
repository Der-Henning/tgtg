import logging
from typing import Union

import apprise

from tgtg_scanner.errors import AppriseConfigurationError, MaskConfigurationError
from tgtg_scanner.models import Config, Favorites, Item, Reservations
from tgtg_scanner.models.reservations import Reservation
from tgtg_scanner.notifiers.base import Notifier

log = logging.getLogger("tgtg")


class Apprise(Notifier):
    """
    Notifier for Apprise. \n
    For more information on Apprise visit\n
    https://github.com/caronc/apprise
    """

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        super().__init__(config, reservations, favorites)
        self.enabled = config.apprise.enabled
        self.title = config.apprise.title
        self.body = config.apprise.body
        self.url = config.apprise.url
        self.cron = config.apprise.cron
        if self.enabled:
            if self.url is None or self.body is None or self.title is None:
                raise AppriseConfigurationError()
            try:
                Item.check_mask(self.title)
                Item.check_mask(self.body)
                Item.check_mask(self.url)
            except MaskConfigurationError as exc:
                raise AppriseConfigurationError(exc.message) from exc

    def _send(self, item: Union[Item, Reservation]) -> None:
        """Sends item information via configured Apprise URL"""
        if isinstance(item, Item):
            if self.url is None or self.body is None or self.title is None:
                raise AppriseConfigurationError()
            url = item.unmask(self.url)
            title = item.unmask(self.title)
            body = item.unmask(self.body)

            log.debug("Apprise url: %s", url)
            log.debug("Apprise title: %s", title)
            log.debug("Apprise body: %s", body)

            apobj = apprise.Apprise()
            apobj.add(self.url)
            apobj.notify(title=title, body=body)
            apobj.clear()

    def __repr__(self) -> str:
        return f"Apprise: {self.url}"
