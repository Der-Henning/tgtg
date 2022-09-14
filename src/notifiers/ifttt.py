import logging
import requests
import json
from models import Item, Config, Cron
from models.errors import IFTTTConfigurationError, MaskConfigurationError
from notifiers import Notifier

log = logging.getLogger('tgtg')


class IFTTT(Notifier):
    """
    Notifier for IFTTT Webhooks.\n
    For more information on IFTTT visit\n
    https://ifttt.com/maker_webhooks
    """
    def __init__(self, config: Config):
        self.enabled = config.ifttt["enabled"]
        self.event = config.ifttt["event"]
        self.key = config.ifttt["key"]
        self.body = config.ifttt["body"]
        self.cron = Cron(config.ifttt["cron"])
        if self.enabled and (not self.event or not self.key):
            raise IFTTTConfigurationError()
        if self.enabled:
            if self.body is None:
                self.body = '{"value1": "${{display_name}}", "value2": ${{items_available}}, "value3": "https://share.toogoodtogo.com/item/${{item_id}}"}'
            try:
                Item.check_mask(self.body)
            except MaskConfigurationError as exc:
                raise IFTTTConfigurationError(exc.message) from exc
        self.url = f"https://maker.ifttt.com/trigger/{self.event}/with/key/{self.key}"

    def send(self, item: Item) -> None:
        """
        Sends item information to the IFTTT webhook endpoint.
        """
        if self.enabled and self.cron.is_now:
            log.debug("Sending IFTTT Notification")
            data = json.loads(item.unmask(self.body).encode(encoding='UTF-8', errors='replace'))
            log.debug("IFTTT data: %s", data)
            requests.post(self.url, timeout=60, json=data)

    def __repr__(self) -> str:
        return f"IFTTT: {self.key}"
