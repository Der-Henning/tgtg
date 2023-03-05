import logging

from models import Config, Item
from models.errors import IFTTTConfigurationError, MaskConfigurationError
from notifiers.webhook import WebHook

log = logging.getLogger('tgtg')


class IFTTT(WebHook):
    """
    Notifier for IFTTT Webhooks.\n
    For more information on IFTTT visit\n
    https://ifttt.com/maker_webhooks
    """

    def __init__(self, config: Config):
        self.enabled = config.ifttt.get("enabled", False)
        self.event = config.ifttt.get("event")
        self.key = config.ifttt.get("key")
        self.body = config.ifttt.get("body")
        self.cron = config.ifttt.get("cron")
        self.timeout = config.ifttt.get("timeout")
        self.headers = {}
        self.method = "POST"
        self.url = (f"https://maker.ifttt.com/trigger/"
                    f"{self.event}/with/key/{self.key}")
        self.type = "application/json"
        self.auth = None

        if self.enabled and (not self.event or not self.key):
            raise IFTTTConfigurationError()
        if self.enabled and self.body is not None:
            try:
                Item.check_mask(self.body)
            except MaskConfigurationError as exc:
                raise IFTTTConfigurationError(exc.message) from exc

    def __repr__(self) -> str:
        return f"IFTTT: {self.key}"
