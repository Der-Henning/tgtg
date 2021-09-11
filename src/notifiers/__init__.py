from notifiers.pushSafer import PushSafer
from notifiers.smtp import SMTP
from notifiers.ifttt import IFTTT
from models import Config, Item


class Notifier():
    def __init__(self, config: Config):
        self.pushSafer = PushSafer(config)
        self.smtp = SMTP(config)
        self.ifttt = IFTTT(config)

    def send(self, item: Item):
        self.pushSafer.send(item)
        self.smtp.send(item)
        self.ifttt.send(item)