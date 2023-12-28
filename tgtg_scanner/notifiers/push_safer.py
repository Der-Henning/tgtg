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
        self.enabled = config.pushsafer.enabled
        self.key = config.pushsafer.key
        self.device_id = config.pushsafer.device_id
        self.cron = config.pushsafer.cron
        if self.enabled:
            if self.key is None or self.device_id is None:
                raise PushSaferConfigurationError()
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
