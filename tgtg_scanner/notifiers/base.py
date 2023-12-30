import logging
import threading
from abc import ABC, abstractmethod
from queue import Queue
from typing import Union

from tgtg_scanner.models import Config, Cron, Favorites, Item, Reservations
from tgtg_scanner.models.reservations import Reservation

log = logging.getLogger("tgtg")


class Notifier(ABC):
    """Base Notifier"""

    @abstractmethod
    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        self.enabled = False
        self.reservations = reservations
        self.favorites = favorites
        self.cron = Cron()
        self.thread = threading.Thread(target=self._run)
        self.queue: Queue[Union[Item, Reservation, None]] = Queue()

    @property
    def name(self):
        """Get notifier name"""
        return self.__class__.__name__

    def _run(self) -> None:
        """Run notifier"""
        while True:
            try:
                item = self.queue.get()
                if item is None:
                    break
                log.debug("Sending %s Notification", self.name)
                self._send(item)
            except KeyboardInterrupt:
                pass
            except Exception as exc:
                log.error("Failed sending %s: %s", self.name, exc)

    def start(self) -> None:
        """Run notifier in thread"""
        if self.enabled:
            log.debug("Starting %s Notifier thread", self.name)
            self.thread.start()

    def send(self, item: Union[Item, Reservation]) -> None:
        """Send notification"""
        if self.enabled and self.cron.is_now:
            self.queue.put(item)
            if not self.thread.is_alive():
                log.debug("%s Notifier thread is dead. Restarting", self.name)
                self.start()

    @abstractmethod
    def _send(self, item: Union[Item, Reservation]) -> None:
        """Send Item information"""
        pass

    def stop(self) -> None:
        """Stop notifier"""
        if self.thread.is_alive():
            log.debug("Stopping %s Notifier thread", self.name)
            self.queue.put(None)
            self.thread.join()
            log.debug("%s Notifier thread stopped", self.name)

    @abstractmethod
    def __repr__(self) -> str:
        pass
