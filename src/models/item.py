import datetime
import re
from .errors import MaskConfigurationError


ATTRS = ["item_id", "items_available", "display_name", "description",
             "price", "currency", "pickupdate", "favorite", "rating",
             "buffet", "item_category", "item_name", "packaging_option",
             "pickup_location", "store_name"]

class Item():
    """
    Takes the raw data from the TGTG API and returns well formated data for notifications.
    """
    def __init__(self, data: dict):
        self.items_available = data.get("items_available", 0)
        self.display_name = data.get("display_name", "-")
        self.favorite = "Yes" if data.get("favorite", False) else "No"
        self.pickup_interval_start = data.get("pickup_interval", {}).get("start", None)
        self.pickup_interval_end = data.get("pickup_interval", {}).get("end", None)
        self.pickup_location = data.get("pickup_location", {}).get("address", {}).get("address_line", "-")

        item = data.get("item", {})
        self.item_id = item.get("item_id")
        self.rating = item.get("average_overall_rating", {}).get("average_overall_rating", None)
        self.rating = "-" if not self.rating else f"{self.rating:.1f}"
        self.packaging_option = item.get("packaging_option", "-")
        self.item_name = item.get("name", "-")
        self.buffet = "Yes" if item.get("buffet", False) else "No"
        self.item_category = item.get("item_category", "-")
        self.description = item.get("description", "-")
        self.price = item.get("price_including_taxes", {}).get("minor_units", 0) / \
            (10**item.get("price_including_taxes", {}).get("decimals", 0))
        self.price = f"{self.price:.2f}"
        self.currency = item.get("price_including_taxes", {}).get("code", "-")

        store = data.get("store", {})
        self.store_name = store.get("name", "-")

    @staticmethod
    def _datetimeparse(datestr: str) -> datetime.datetime:
        """
        Formates datetime string from tgtg api
        """
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        value = datetime.datetime.strptime(datestr, fmt)
        return value.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

    @staticmethod
    def check_mask(text: str) -> None:
        """
        Checks whether the variables in the provided string are available

        Raises MaskConfigurationError
        """
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", text):
            if not match.group(1) in ATTRS:
                raise MaskConfigurationError(match.group(0))

    def unmask(self, text: str) -> str:
        """
        Replaces variables with the current values.
        """
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", text):
            if hasattr(self, match.group(1)):
                text = text.replace(match.group(0), str(getattr(self, match.group(1))))
        return text

    @property
    def pickupdate(self) -> str:
        """
        Returns a well formated string, providing the pickup time range
        """
        if (self.pickup_interval_start and self.pickup_interval_end):
            now = datetime.datetime.now()
            pfrom = self._datetimeparse(self.pickup_interval_start)
            pto = self._datetimeparse(self.pickup_interval_end)
            prange = f"{pfrom.hour:02d}:{pfrom.minute:02d} - {pto.hour:02d}:{pto.minute:02d}"
            if now.date() == pfrom.date():
                return f"Today, {prange}"
            if (pfrom.date() - now.date()).days == 1:
                return f"Tomorrow, {prange}"
            return f"{pfrom.day}/{pfrom.month}, {prange}"
        return "-"
