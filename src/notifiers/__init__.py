import logging
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
            log.info("- Telegram: %s", self.telegram.chat_ids)

    def send(self, item: Item) -> None:
        """
        Send Notification on all notifiers
        """
        try:
            self.push_safer.send(item)
        except Exception as err:
            log.error('Failed sending Push Safer Notification: %s', err)
        try:
            self.smtp.send(item)
        except Exception as err:
            log.error('Failed sending SMTP Notification: %s', err)
        try:
            self.ifttt.send(item)
        except Exception as err:
            log.error('Failed sending IFTTT Notification: %s', err)
        try:
            self.webhook.send(item)
        except Exception as err:
            log.error('Failed sending WebHook Notification: %s', err)
        try:
            self.telegram.send(item)
        except Exception as err:
            log.error('Failed sending Telegram Notification: %s', err)
