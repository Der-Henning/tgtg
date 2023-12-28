import logging
from typing import Union

from pushsafer import Client

from tgtg_scanner.errors import PushSaferConfigurationError
from tgtg_scanner.models import Config, Favorites, Item, Reservations
from tgtg_scanner.models.reservations import Reservation
from tgtg_scanner.notifiers.base import Notifier

log = logging.getLogger("tgtg")


class PushSafer(Notifier):
    """
    Notifier for PushSafer\n
    For more information visit:\n
    https://www.pushsafer.com/
    """

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        super().__init__(config, reservations, favorites)
        self.enabled = config.push_safer.get("enabled", False)
        self.key = config.push_safer.get("key")
        self.device_id = config.push_safer.get("deviceId")
        self.cron = config.push_safer.get("cron")
        if self.enabled and (not self.key or not self.device_id):
            raise PushSaferConfigurationError()
        if self.enabled:
            self.client = Client(self.key)

    def _send(self, item: Union[Item, Reservation]) -> None:
        """
        Sends item information to the Pushsafer endpoint.
        """
        if isinstance(item, Item):
            message = f"New Amount: {item.items_available}"
            self.client.send_message(message, item.display_name, self.device_id)

    def __repr__(self) -> str:
        return f"PushSafer: {self.key}"
