import logging

from tgtg_scanner.errors import IFTTTConfigurationError, MaskConfigurationError
from tgtg_scanner.models import Config, Favorites, Item, Reservations
from tgtg_scanner.notifiers.webhook import WebHook

log = logging.getLogger("tgtg")


class IFTTT(WebHook):
    """
    Notifier for IFTTT Webhooks.\n
    For more information on IFTTT visit\n
    https://ifttt.com/maker_webhooks
    """

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        super(WebHook, self).__init__(config, reservations, favorites)
        self.enabled = config.ifttt.enabled
        self.event = config.ifttt.event
        self.key = config.ifttt.key
        self.body = config.ifttt.body
        self.cron = config.ifttt.cron
        self.timeout = config.ifttt.timeout
        self.headers = {}
        self.method = "POST"
        self.url = f"https://maker.ifttt.com/trigger/" f"{self.event}/with/key/{self.key}"
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
