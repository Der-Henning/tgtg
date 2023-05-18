import logging

from models import Config, Item
from models.errors import ScriptConfigurationError, MaskConfigurationError
from notifiers import Notifier

log = logging.getLogger('tgtg')


class Script(Notifier):
    """Notifier for the script output"""

    def __init__(self, config: Config):
        self.enabled = config.script.get("enabled", False)
        self.command = config.script.get("command")
        self.timeout = config.script.get("timeout", 60)
        self.cron = config.script.get("cron")

        if self.enabled:
            try:
                Item.check_mask(self.command)
            except MaskConfigurationError as exc:
                raise ScriptConfigurationError(exc.message) from exc


    def _send(self, item: Item) -> None:
        import subprocess
        subprocess.Popen(self.command.split())


    def __repr__(self) -> str:
        return f"Shell script: {self.command}"
