import logging
from typing import Type, Union

from tgtg_scanner.models import Config, Cron, Favorites, Item, Reservations
from tgtg_scanner.models.reservations import Reservation
from tgtg_scanner.notifiers.apprise import Apprise
from tgtg_scanner.notifiers.base import Notifier
from tgtg_scanner.notifiers.console import Console
from tgtg_scanner.notifiers.ifttt import IFTTT
from tgtg_scanner.notifiers.ntfy import Ntfy
from tgtg_scanner.notifiers.push_safer import PushSafer
from tgtg_scanner.notifiers.script import Script
from tgtg_scanner.notifiers.smtp import SMTP
from tgtg_scanner.notifiers.telegram import Telegram
from tgtg_scanner.notifiers.webhook import WebHook

log = logging.getLogger("tgtg")

NOTIFIERS: list[Type[Notifier]] = [Apprise, Console, PushSafer, SMTP, IFTTT, Ntfy, WebHook, Telegram, Script]


class Notifiers:
    """Notifier Manager"""

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        self._notifiers: list[Notifier] = [NotifierCls(config, reservations, favorites) for NotifierCls in NOTIFIERS]
        log.info("Activated notifiers:")
        if self.notifier_count == 0:
            log.warning("No notifiers configured!")
        for notifier in self._enabled_notifiers:
            log.info("- %s", notifier)
            if notifier.cron != Cron("* * * * *"):
                log.info("  Schedule: %s", notifier.cron.get_description(config.locale))

    @property
    def _enabled_notifiers(self) -> list[Notifier]:
        return [notifier for notifier in self._notifiers if notifier.enabled]

    @property
    def notifier_count(self) -> int:
        """Number of enabled notifiers

        Returns:
            int: notifier count
        """
        return len(self._enabled_notifiers)

    def send(self, item: Union[Item, Reservation]) -> None:
        """Send notifications on all enabled notifiers.

        Args:
            item (Item, Reservation): Item information to send
        """
        for notifier in self._notifiers:
            notifier.send(item)

    def start(self) -> None:
        """Start all notifiers"""
        for notifier in self._notifiers:
            try:
                notifier.start()
            except Exception as exc:
                log.warning("Error starting %s - %s", notifier, exc)

    def stop(self) -> None:
        """Stop all notifiers"""
        for notifier in self._notifiers:
            try:
                notifier.stop()
            except Exception as exc:
                log.warning("Error stopping %s - %s", notifier, exc)
