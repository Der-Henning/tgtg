import logging

from models import Config, Item, Order
from models.errors import ConsoleConfigurationError, MaskConfigurationError
from notifiers.base import Notifier

log = logging.getLogger('tgtg')


class Console(Notifier):
    """Notifier for the console output"""

    def __init__(self, config: Config):
        Notifier.__init__(self, config)
        self.enabled = config.console.get("enabled", False)
        self.body = config.console.get("body")
        self.cron = config.console.get("cron")

        if self.enabled:
            try:
                Item.check_mask(self.body)
            except MaskConfigurationError as exc:
                raise ConsoleConfigurationError(exc.message) from exc

    def _send_item(self, item: Item) -> None:
        message = item.unmask(self.body)
        print(message)

    def _send_order(self, order: Order) -> None:
        """Send Order information"""

    def __repr__(self) -> str:
        return "Console stdout"
