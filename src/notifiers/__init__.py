import logging
from notifiers.push_safer import PushSafer
from notifiers.smtp import SMTP
from notifiers.ifttt import IFTTT
from models import Config, Item

log = logging.getLogger('tgtg')


class Notifiers():
    def __init__(self, config: Config):
        self.push_safer = PushSafer(config)
        self.smtp = SMTP(config)
        self.ifttt = IFTTT(config)
        log.info("Activated notifiers:")
        if self.smtp.enabled:
            log.info("- SMTP: %s", self.smtp.recipient)
        if self.ifttt.enabled:
            log.info("- IFTTT: %s", self.ifttt.key)
        if self.push_safer.enabled:
            log.info("- PushSafer: %s", self.push_safer.key)
        test_item = Item({"item": {"item_id": "12345"},
                        "display_name": "test_item",
                        "items_available": 1})
        log.info("Sending test notifications ...")
        self.send(test_item)

    def send(self, item: Item):
        self.push_safer.send(item)
        self.smtp.send(item)
        self.ifttt.send(item)
