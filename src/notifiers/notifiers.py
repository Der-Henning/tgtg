import logging
from typing import List
from notifiers.base import Notifier
from notifiers.push_safer import PushSafer
from notifiers.smtp import SMTP
from notifiers.ifttt import IFTTT
from notifiers.webhook import WebHook
from notifiers.telegram import Telegram
from models import Config, Item

log = logging.getLogger('tgtg')


class Notifiers():
    def __init__(self, config: Config):
        self._notifiers: List[Notifier] = [
            PushSafer(config),
            SMTP(config),
            IFTTT(config),
            WebHook(config),
            Telegram(config)
        ]
        enabled_notifiers = [notifier for notifier in self._notifiers if notifier.enabled]
        log.info("Activated notifiers:")
        if len(enabled_notifiers) == 0:
            log.warning("No notifiers configured!")
        for notifier in enabled_notifiers:
            log.info("- %s", notifier)
            if notifier.cron.cron != '* * * * *':
                log.info("  Schedule: %s", notifier.cron.description)

    def send(self, item: Item) -> None:
        """
        Send Notification on all notifiers
        """
        for notifier in self._notifiers:
            try:
                notifier.send(item)
            except Exception as exc:
                log.error('Failed sending %s: %s', notifier, exc)

    def stop(self):
        """Stop all notifiers"""
        for notifier in self._notifiers:
            try:
                notifier.stop()
            except Exception as exc:
                log.warning("Error stopping %s - %s", notifier, exc)
