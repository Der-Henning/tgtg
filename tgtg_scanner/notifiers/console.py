import logging

from tgtg_scanner.errors import ConsoleConfigurationError, MaskConfigurationError
from tgtg_scanner.models import Config, Favorites, Item, Reservations
from tgtg_scanner.models.reservations import Reservation
from tgtg_scanner.notifiers.base import Notifier

log = logging.getLogger("tgtg")


class Console(Notifier):
    """Notifier for the console output."""

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        super().__init__(config, reservations, favorites)
        self.enabled = config.console.enabled
        self.body = config.console.body
        self.cron = config.console.cron

        if self.enabled:
            try:
                Item.check_mask(self.body)
            except MaskConfigurationError as exc:
                raise ConsoleConfigurationError(exc.message) from exc

    def _send(self, item: Item | Reservation) -> None:
        if isinstance(item, Item):
            message = item.unmask(self.body)
            print(message)

    def __repr__(self) -> str:
        return "Console stdout"
