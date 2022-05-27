import logging
import requests
from models import Item, Config
from models.errors import IFTTTConfigurationError

log = logging.getLogger('tgtg')

class IFTTT():
    """
    Notifier for IFTTT Webhooks.\n
    For more information on IFTTT visit\n
    https://ifttt.com/maker_webhooks
    """
    def __init__(self, config: Config):
        self.enabled = config.ifttt["enabled"]
        self.event = config.ifttt["event"]
        self.key = config.ifttt["key"]
        if self.enabled and (not self.event or not self.key):
            raise IFTTTConfigurationError()
        self.url = f"https://maker.ifttt.com/trigger/{self.event}/with/key/{self.key}"

    def send(self, item: Item) -> None:
        """
        Sends item information to the IFTTT webhook endpoint.
        """
        if self.enabled:
            log.debug("Sending IFTTT Notification")
            requests.post(self.url,
                          json={"value1": item.display_name,
                                "value2": item.items_available},
                          timeout=60)
