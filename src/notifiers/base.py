import logging
from abc import ABC, abstractmethod

from models import Config, Item, Order

log = logging.getLogger('tgtg')


class Notifier(ABC):
    messages = []
    enabled_notify_ext = None

    def __init__(self, config: Config):
        # only on first run of any notifier
        self.enabled_notify_ext = config.notify_ext.get("enabled")
        if self.messages == []:
            self.messages.append(config.notify_ext.get("body_1"))
            self.messages.append(config.notify_ext.get("body_2"))
            self.messages.append(config.notify_ext.get("body_3"))

    @property
    def name(self):
        return self.__class__.__name__

    def send_item(self, item: Item) -> None:
        if self._should_send_notification():
            self._send_item(item)

    def send_order(self, order: Order, index: int) -> None:
        if self._should_send_notification():
            self._send_order(order, self.messages[index])

    def _should_send_notification(self) -> bool:
        if self.enabled and self.cron.is_now:
            log.debug("Sending %s Notification", self.name)
            return True
        return False

    @abstractmethod
    def _send_item(self, item: Item) -> None:
        """Send Item information"""

    @abstractmethod
    def _send_order(self, order: Order, message: str) -> None:
        """Send Order information"""

    def stop(self) -> None:
        """Stop notifier"""
