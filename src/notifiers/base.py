import logging
from abc import ABC, abstractmethod

from models import Config, Item, Order
from models.reservations import Reservation

log = logging.getLogger('tgtg')


class Notifier(ABC):
    messages = []
    enabled_notify_ext = None

    def __init__(self, config: Config):
        self.enabled_notify_ext = config.notify_ext.get("enabled")
        # only on first run of any notifier
        if self.messages == []:
            self.messages.append(config.notify_ext.get("body_1"))
            self.messages.append(config.notify_ext.get("body_2"))
            self.messages.append(config.notify_ext.get("body_3"))

    @property
    def name(self):
        """Get notifier name"""
        return self.__class__.__name__

    def send_item(self, item: Item) -> None:
        """Send notification for new item"""
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

    def send_reservation(self, reservation: Reservation) -> None:
        """Send notification for new reservation

        Args:
            reservation (Reservation): Reservation to send
        """
        if self.enabled:
            log.debug("Sending %s new Reservation", self.name)
            self._send_reservation(reservation)

    @abstractmethod
    def _send_item(self, item: Item) -> None:
        """Send Item information"""

    def _send_reservation(self, reservation: Reservation) -> None:
        pass

    @abstractmethod
    def _send_order(self, order: Order, message: str) -> None:
        """Send Order information"""

    def stop(self) -> None:
        """Stop notifier"""
