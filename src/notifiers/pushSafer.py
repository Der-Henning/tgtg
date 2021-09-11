from pushsafer import init, Client
from models import Item, Config


class PushSafer():
    def __init__(self, config: Config):
        self.key = config.pushSafer["key"]
        self.deviceId = config.pushSafer["deviceId"]
        self.enabled = config.pushSafer["enabled"]
        if self.enabled:
            init(self.key)
            self._test()

    def _test(self):
        if self.enabled:
            message = f"This is a Test. If you receive this message you will receive notifications for new magic bags."
            Client("").send_message(message, "Test Notification", self.deviceId,
                                    "", "", "", "", "", "", "", "", "", "", "", "", "")

    def send(self, item: Item):
        if self.enabled:
            message = f"New Amount: {item.items_available}"
            Client("").send_message(message, item.display_name, self.deviceId,
                                    "", "", "", "", "", "", "", "", "", "", "", "", "")
