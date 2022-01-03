import logging
from pushsafer import Client
from models import Item, Config, PushSaferConfigurationError

log = logging.getLogger('tgtg')


class PushSafer():
    def __init__(self, config: Config):
        self.key = config.push_safer["key"]
        self.device_id = config.push_safer["deviceId"]
        self.enabled = config.push_safer["enabled"]
        if self.enabled and (not self.key or not self.device_id):
            raise PushSaferConfigurationError()
        if self.enabled:
            self.client = Client(self.key)

    def send(self, item: Item):
        if self.enabled:
            log.info("Sending PushSafer Notification")
            message = f"New Amount: {item.items_available}"
            self.client.send_message(message, item.display_name, self.device_id,
                                     "", "", "", "", "", "", "", "", "", "", "", "", "")
