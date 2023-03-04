import logging
from typing import List

from models import Config, Item
from notifiers.apprise import Apprise
from notifiers.base import Notifier
from notifiers.console import Console
from notifiers.ifttt import IFTTT
from notifiers.push_safer import PushSafer
from notifiers.smtp import SMTP
from notifiers.telegram import Telegram
from notifiers.webhook import WebHook

log = logging.getLogger("tgtg")


class Notifiers:
    def __init__(self, config: Config):
        self._notifiers: List[Notifier] = [
            Apprise(config),
            Console(config),
            PushSafer(config),
            SMTP(config),
            IFTTT(config),
            WebHook(config),
            Telegram(config),
        ]
        log.info("Activated notifiers:")
        if self.notifier_count == 0:
            log.warning("No notifiers configured!")
        for notifier in self._enabled_notifiers:
            log.info("- %s", notifier)
            if notifier.cron.cron != "* * * * *":
                log.info("  Schedule: %s", notifier.cron.description)

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

    def stop(self):
        """Stop all notifiers"""
        for notifier in self._notifiers:
            try:
                notifier.stop()
            except Exception as exc:
                log.warning("Error stopping %s - %s", notifier, exc)
