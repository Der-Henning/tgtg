import logging
from pushsafer import Client
from models import Item, Config, Cron
from models.errors import PushSaferConfigurationError
from notifiers import Notifier

log = logging.getLogger('tgtg')


class PushSafer(Notifier):
    """
    Notifier for PushSafer\n
    For more information visit:\n
    https://www.pushsafer.com/
    """
    def __init__(self, config: Config):
        self.key = config.push_safer["key"]
        self.device_id = config.push_safer["deviceId"]
        self.enabled = config.push_safer["enabled"]
        self.cron = Cron(config.push_safer["cron"])
        if self.enabled and (not self.key or not self.device_id):
            raise PushSaferConfigurationError()
        if self.enabled:
            self.client = Client(self.key)

    def send(self, item: Item) -> None:
        """
        Sends item information to the Pushsafer endpoint.
        """
        if self.enabled and self.cron.is_now:
            log.debug("Sending PushSafer Notification")
            message = f"New Amount: {item.items_available}"
            self.client.send_message(message, item.display_name, self.device_id,
                                     "", "", "", "", "", "", "", "", "", "", "", "", "")

    def __repr__(self) -> str:
        return f"PushSafer: {self.key}"
