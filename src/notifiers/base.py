import logging
from abc import ABC, abstractmethod

from models import Config, Cron, Item

log = logging.getLogger('tgtg')


class Notifier(ABC):
    @abstractmethod
    def __init__(self, config: Config):
        self.enabled = False
        self.cron = Cron()

    def send(self, item: Item) -> None:
        if self.enabled and self.cron.is_now:
            log.debug("Sending %s Notification", self.__class__.__name__)
            self._send(item)

    @abstractmethod
    def _send(self, item: Item) -> None:
        """Send Item information"""

    def stop(self) -> None:
        """Stop notifier"""
