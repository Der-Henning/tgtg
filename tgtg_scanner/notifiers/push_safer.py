import logging

from pushsafer import Client

from tgtg_scanner.errors import PushSaferConfigurationError
from tgtg_scanner.models import Config, Favorites, Item, Reservations
from tgtg_scanner.models.reservations import Reservation
from tgtg_scanner.notifiers.base import Notifier

log = logging.getLogger("tgtg")


class PushSafer(Notifier):
    """Notifier for PushSafer

    For more information visit https://www.pushsafer.com/.
    """

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        super().__init__(config, reservations, favorites)
        self.enabled = config.pushsafer.enabled
        self.key = config.pushsafer.key
        self.device_ids = config.pushsafer.device_ids
        self.cron = config.pushsafer.cron
        if self.enabled:
            if self.key is None or len(self.device_ids) == 0:
                raise PushSaferConfigurationError()
            self.client = Client(self.key)

    def _send(self, item: Item | Reservation) -> None:
        """Sends item information to the Pushsafer endpoint."""
        if isinstance(item, Item):
            message = f"New Amount: {item.items_available}"
            for device_id in self.device_ids:
                self.client.send_message(message, item.display_name, device_id)

    def __repr__(self) -> str:
        return f"PushSafer: {self.key}"
