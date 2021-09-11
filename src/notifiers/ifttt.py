import requests
from models import Item, Config
import logging as log


class IFTTT():
    def __init__(self, config: Config):
        self.enabled = config.ifttt["enabled"]
        self.url = "https://maker.ifttt.com/trigger/{0}/with/key/{1}".format(
            config.ifttt["event"], config.ifttt["key"])
        if self.enabled:
            self._test()
        

    def _test(self):
        if self.enabled:
            log.info("Sending Test IFTTT Notification")
            requests.post(self.url, json={
                          "value1": "Test Notification", "value2": 0})

    def send(self, item: Item):
        if self.enabled:
            log.info("Sending IFTTT Notification")
            requests.post(self.url, json={
                          "value1": item.display_name, "value2": item.items_available})
