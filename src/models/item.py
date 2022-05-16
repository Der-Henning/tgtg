import datetime
import re
from .errors import MaskConfigurationError


ATTRS = ["item_id", "items_available", "display_name", "description",
             "price", "currency", "pickupdate", "favorite", "rating"]

class Item():
    item_id: str
    items_available: int
    display_name: str = None
    price: float = 0.0
    currency: str = None
    favorite: bool = False
    description: str = None
    rating: float = 0.0

    def __init__(self, data: dict):
        self.item_id = data["item"]["item_id"]
        self.items_available = data["items_available"]
        self.display_name = data["display_name"]
        self.favorite = data["favorite"]
        self.price = 0
        self.currency = ""
        if 'price_including_taxes' in data["item"]:
            self.price = data["item"]["price_including_taxes"]["minor_units"] / \
                (10**data["item"]["price_including_taxes"]["decimals"])
            self.currency = data["item"]["price_including_taxes"]["code"]
        if 'pickup_interval' in data:
            self.interval_start = data['pickup_interval']['start']
            self.interval_end = data['pickup_interval']['end']
        if 'average_overall_rating' in data["item"]:
            self.rating = round(data["item"]["average_overall_rating"]["average_overall_rating"], 1)
        if 'description' in data["item"]:
            self.description = data["item"]["description"]

    @staticmethod
    def _datetimeparse(datestr: str) -> datetime.datetime:
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        value = datetime.datetime.strptime(datestr, fmt)
        return value.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

    @staticmethod
    def check_mask(text) -> None:
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", text):
            if not match.group(1) in ATTRS:
                raise MaskConfigurationError(match.group(0))

    def unmask(self, text: str) -> str:
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", text):
            if hasattr(self, match.group(1)):
                text = text.replace(match.group(0), str(getattr(self, match.group(1))))
        return text

    @property
    def pickupdate(self):
        if (hasattr(self, "interval_start") and hasattr(self, "interval_end")):
            now = datetime.datetime.now()
            pfrom = self._datetimeparse(self.interval_start)
            pto = self._datetimeparse(self.interval_end)
            prange = "%02d:%02d - %02d:%02d" % (pfrom.hour,
                                                pfrom.minute, pto.hour, pto.minute)
            if now.date() == pfrom.date():
                return "Today, %s" % prange
            elif (pfrom.date() - now.date()).days == 1:
                return "Tomorrow, %s" % prange
            return "%d/%d, %s" % (pfrom.day, pfrom.month, prange)
        return None
