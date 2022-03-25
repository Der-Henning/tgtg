import logging
from datetime import datetime
from notifiers.push_safer import PushSafer
from notifiers.smtp import SMTP
from notifiers.ifttt import IFTTT
from notifiers.webhook import WebHook
from notifiers.telegram import Telegram
from models import Config, Item

log = logging.getLogger('tgtg')


class Notifiers():
    def __init__(self, config: Config):
        self.push_safer = PushSafer(config)
        self.smtp = SMTP(config)
        self.ifttt = IFTTT(config)
        self.webhook = WebHook(config)
        self.telegram = Telegram(config)
        log.info("Activated notifiers:")
        if self.smtp.enabled:
            log.info("- SMTP: %s", self.smtp.recipient)
        if self.ifttt.enabled:
            log.info("- IFTTT: %s", self.ifttt.key)
        if self.push_safer.enabled:
            log.info("- PushSafer: %s", self.push_safer.key)
        if self.webhook.enabled:
            log.info("- WebHook: %s", self.webhook.url)
        if self.telegram.enabled:
            log.info("- Telegram: %s", self.telegram.chat_id)
        now = datetime.now()
        if not config.disable_tests:
            test_item = Item({
                "item": {
                    "item_id": "12345",
                    "price_including_taxes": {
                        "code": "EUR",
                        "minor_units": 1099,
                        "decimals": 2
                    }
                },
                "display_name": "test_item",
                "pickup_interval": {
                    "start": f"{now.year}-{now.month}-{now.day}T20:00:00Z",
                    "end": f"{now.year}-{now.month}-{now.day}T21:00:00Z"},
                "items_available": 1})
            log.info("Sending test notifications ...")
            self.send(test_item)

    def send(self, item: Item):
        try:
            self.push_safer.send(item)
        except Exception as err:
            log.error(err)
        try:
            self.smtp.send(item)
        except Exception as err:
            log.error(err)
        try:
            self.ifttt.send(item)
        except Exception as err:
            log.error(err)
        try:
            self.webhook.send(item)
        except Exception as err:
            log.error(err)
        try:
            self.telegram.send(item)
        except Exception as err:
            log.error(err)
