from notifiers.pushSafer import PushSafer
from notifiers.smtp import SMTP
from notifiers.ifttt import IFTTT
from models import Config, Item
import logging

log = logging.getLogger('tgtg')


class Notifiers():
    def __init__(self, config: Config):
        self.pushSafer = PushSafer(config)
        self.smtp = SMTP(config)
        self.ifttt = IFTTT(config)
        log.info(f"Activated notifiers:")
        if self.smtp.enabled:
            log.info(f"- SMTP: {self.smtp.recipient}")
        if self.ifttt.enabled:
            log.info(f"- IFTTT: {self.ifttt.key}")
        if self.pushSafer.enabled:
            log.info(f"- PushSafer: {self.pushSafer.key}")
        testItem = Item({"item": {"item_id": "12345"},
                        "display_name": "test_item",
                        "items_available": 1})
        log.info("Sending test notifications ...")
        self.send(testItem)

    def send(self, item: Item):
        self.pushSafer.send(item)
        self.smtp.send(item)
        self.ifttt.send(item)
