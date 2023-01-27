from abc import ABC, abstractmethod

from models import Config, Cron, Item


class Notifier(ABC):
    @abstractmethod
    def __init__(self, config: Config):
        self.enabled = False
        self.cron = Cron()

    @abstractmethod
    def send(self, item: Item) -> None:
        """Send Item information"""

    def stop(self):
        """Stop notifier"""
