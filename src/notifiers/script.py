import logging

from models import Config, Item
from models.errors import ScriptConfigurationError, MaskConfigurationError
from notifiers import Notifier

log = logging.getLogger('tgtg')


class Script(Notifier):
    """Notifier for the script output"""

    def __init__(self, config: Config):
        self.enabled = config.console.get("enabled", False)
        self.command = config.console.get("command")

        if self.enabled:
            try:
                Item.check_mask(self.command)
            except MaskConfigurationError as exc:
                raise ScriptConfigurationError(exc.message) from exc


    def _send(self, item: Item) -> None:
        import subprocess
        subprocess.call([self.command])


    def __repr__(self) -> str:
        return " "
