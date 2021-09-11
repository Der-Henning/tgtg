from tgtg import TgtgClient
from models import Config


class Helper():
    def __init__(self):
        self.config = Config()
        self.tgtg_client = TgtgClient(
            email=self.config.tgtg.username, password=self.config.tgtg.password)

    def _getItems(self, lat, lng, radius):
        return self.tgtg_client.get_items(
            favorites_only=False,
            latitude=lat,
            longitude=lng,
            radius=radius,
        )
