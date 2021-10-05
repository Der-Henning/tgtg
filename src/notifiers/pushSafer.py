from pushsafer import init, Client
from models import Item, Config, PushSaferConfigurationError
import logging

log = logging.getLogger('tgtg')


class PushSafer():
    def __init__(self, config: Config):
        self.key = config.pushSafer["key"]
        self.deviceId = config.pushSafer["deviceId"]
        self.enabled = config.pushSafer["enabled"]
        if self.enabled and (not self.key or not self.deviceId):
            raise PushSaferConfigurationError()
        if self.enabled:
            init(self.key)

    def send(self, item: Item):
        if self.enabled:
            log.info("Sending PushSafer Notification")
            message = f"New Amount: {item.items_available}"
            Client("").send_message(message, item.display_name, self.deviceId,
                                    "", "", "", "", "", "", "", "", "", "", "", "", "")
