import logging
from abc import ABC, abstractmethod

from models import Config, Cron, Item
from models.reservations import Reservation

log = logging.getLogger('tgtg')


class Notifier(ABC):
    @abstractmethod
    def __init__(self, config: Config):
        self.enabled = False
        self.cron = Cron()

    @property
    def name(self):
        """Get notifier name"""
        return self.__class__.__name__

    def send(self, item: Item) -> None:
        """Send notification for new item"""
        if self.enabled and self.cron.is_now:
            log.debug("Sending %s Notification", self.name)
            self._send(item)

    def send_reservation(self, reservation: Reservation) -> None:
        """Send notification for new reservation

        Args:
            reservation (Reservation): Reservation to send
        """
        if self.enabled:
            log.debug("Sending %s new Reservation", self.name)
            self._send_reservation(reservation)

    @abstractmethod
    def _send(self, item: Item) -> None:
        """Send Item information"""

    def _send_reservation(self, reservation: Reservation) -> None:
        pass

    def stop(self) -> None:
        """Stop notifier"""
