import requests
from models import Item, Config, IFTTTConfigurationError
import logging as log


class IFTTT():
    def __init__(self, config: Config):
        self.enabled = config.ifttt["enabled"]
        self.event = config.ifttt["event"]
        self.key = config.ifttt["key"]
        if self.enabled and (not self.event or not self.key):
            raise IFTTTConfigurationError()
        self.url = "https://maker.ifttt.com/trigger/{0}/with/key/{1}".format(
            self.event, self.key)

    def send(self, item: Item):
        if self.enabled:
            log.info("Sending IFTTT Notification")
            requests.post(self.url, json={
                          "value1": item.display_name, "value2": item.items_available})
