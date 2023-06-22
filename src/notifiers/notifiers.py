import logging
from typing import List

from models import Config, Cron, Item, Reservations
from models.reservations import Reservation
from notifiers.apprise import Apprise
from notifiers.base import Notifier
from notifiers.console import Console
from notifiers.ifttt import IFTTT
from notifiers.ntfy import Ntfy
from notifiers.push_safer import PushSafer
from notifiers.script import Script
from notifiers.smtp import SMTP
from notifiers.telegram import Telegram
from notifiers.webhook import WebHook

log = logging.getLogger("tgtg")


class Notifiers:
    def __init__(self, config: Config, reservations: Reservations):
        self._notifiers: List[Notifier] = [
            Apprise(config),
            Console(config),
            PushSafer(config),
            SMTP(config),
            IFTTT(config),
            Ntfy(config),
            WebHook(config),
            Telegram(config, reservations),
            Script(config),
        ]
        log.info("Activated notifiers:")
        if self.notifier_count == 0:
            log.warning("No notifiers configured!")
        for notifier in self._enabled_notifiers:
            log.info("- %s", notifier)
            if notifier.cron != Cron("* * * * *"):
                log.info("  Schedule: %s",
                         notifier.cron.get_description(config.locale))

    @property
    def _enabled_notifiers(self) -> List[Notifier]:
        return [notifier for notifier in self._notifiers if notifier.enabled]

    @property
    def notifier_count(self) -> int:
        """Number of enabled notifiers

        Returns:
            int: notifier count
        """
        return len(self._enabled_notifiers)

    def send(self, item: Item) -> None:
        """Send notifications on all enabled notifiers.

        Args:
            item (Item): Item information to send
        """
        for notifier in self._enabled_notifiers:
            try:
                notifier.send(item)
            except Exception as exc:
                log.error("Failed sending %s: %s", notifier, exc)

    def send_reservation(self, reservation: Reservation) -> None:
        """Send notification for new reservation

        Args:
            reservation (Reservation): New reservation
        """
        for notifier in self._enabled_notifiers:
            try:
                notifier.send_reservation(reservation)
            except Exception as exc:
                log.error("Failed sending %s: %s", notifier, exc)

    def stop(self) -> None:
        """Stop all notifiers"""
        for notifier in self._notifiers:
            try:
                notifier.stop()
            except Exception as exc:
                log.warning("Error stopping %s - %s", notifier, exc)
