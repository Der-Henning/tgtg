import logging
import subprocess

from models import Config, Item
from models.errors import MaskConfigurationError, ScriptConfigurationError
from models.order import Order
from notifiers import Notifier

log = logging.getLogger('tgtg')


class Script(Notifier):
    """Notifier for the script output"""

    def __init__(self, config: Config):
        Notifier.__init__(self, config)
        self.enabled = config.script.get("enabled", False)
        self.command = config.script.get("command")
        self.cron = config.script.get("cron")

        if self.enabled and (not self.command):
            raise ScriptConfigurationError()
        if self.enabled:
            try:
                Item.check_mask(self.command)
            except MaskConfigurationError as exc:
                raise ScriptConfigurationError(exc.message) from exc

    def _send_item(self, item: Item) -> None:
        args = [item.unmask(arg) for arg in self.command.split()]
        subprocess.Popen(args)

    def _send_order(self, order: Order, message_body: str) -> None:
        """Send Order information"""

    def __repr__(self) -> str:
        return f"Shell script: {self.command}"
