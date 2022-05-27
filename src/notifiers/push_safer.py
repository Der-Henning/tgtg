import logging
from pushsafer import Client
from models import Item, Config
from models.errors import PushSaferConfigurationError

log = logging.getLogger('tgtg')


class PushSafer():
    """
    Notifier for PushSafer\n
    For more information visit:\n
    https://www.pushsafer.com/
    """
    def __init__(self, config: Config):
        self.key = config.push_safer["key"]
        self.device_id = config.push_safer["deviceId"]
        self.enabled = config.push_safer["enabled"]
        if self.enabled and (not self.key or not self.device_id):
            raise PushSaferConfigurationError()
        if self.enabled:
            self.client = Client(self.key)

    def send(self, item: Item) -> None:
        """
        Sends item information to the Pushsafer endpoint.
        """
        if self.enabled:
            log.debug("Sending PushSafer Notification")
            message = f"New Amount: {item.items_available}"
            self.client.send_message(message, item.display_name, self.device_id,
                                     "", "", "", "", "", "", "", "", "", "", "", "", "")
