import datetime
import logging
from http import HTTPStatus

import humanize
import requests

from models.location import Location
from models.order_item_base import Order_Item_Base
from shared import DATETIME_FORMAT

ITEM_ATTRS = [
    "item_id", "items_available", "display_name", "description",
    "price", "currency", "pickupdate", "favorite", "rating",
    "buffet", "item_category", "item_name", "item_logo", "item_cover",
    "scanned_on", "item_logo_bytes", "item_cover_bytes", "link"
]

log = logging.getLogger('tgtg')


class Item(Order_Item_Base):
    ATTRS = Order_Item_Base.ATTRS + ITEM_ATTRS
    """
    Takes the raw data from the TGTG API and
    returns well formated data for notifications.
    """

    def __init__(self, data: dict, location: Location = None):
        super().__init__(data, location)
        self.is_order = False
        self.items_available = data.get("items_available", 0)
        self.display_name = data.get("display_name", "-")
        self.favorite = "Yes" if data.get("favorite", False) else "No"

        item = data.get("item", {})
        self.rating = item.get("average_overall_rating", {}).get(
            "average_overall_rating", None)
        self.rating = "-" if not self.rating else f"{self.rating:.1f}"
        self.packaging_option = item.get("packaging_option", "-")
        self.item_name = item.get("name", "-")
        self.buffet = "Yes" if item.get("buffet", False) else "No"
        self.item_category = item.get("item_category", "-")
        self.description = item.get("description", "-")
        price_including_taxes = item.get("price_including_taxes", {})
        self.price = (price_including_taxes.get("minor_units", 0) /
                      10**price_including_taxes.get("decimals", 0))
        self.price = f"{self.price:.2f}"
        self.currency = item.get("price_including_taxes", {}).get("code", "-")
        self.item_logo = item.get("logo_picture", {}).get(
            "current_url",
            "https://tgtg-mkt-cms-prod.s3.eu-west-1.amazonaws.com/"
            "13512/TGTG_Icon_White_Cirle_1988x1988px_RGB.png")
        self.item_cover = item.get("cover_picture", {}).get(
            "current_url",
            "https://images.tgtg.ninja/standard_images/GENERAL/other1.jpg")

        store = data.get("store", {})
        self.store_name = store.get("name", "-")

        self.scanned_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _datetimeparse(datestr: str) -> datetime.datetime:
        """
        Formates datetime string from tgtg api
        """
        fmt = DATETIME_FORMAT
        value = datetime.datetime.strptime(datestr, fmt)
        return value.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

    @staticmethod
    def get_image(url: str) -> bytes:
        response = requests.get(url)
        if not response.status_code == HTTPStatus.OK:
            log.warning("Get Image Error: %s - %s",
                        response.status_code,
                        response.content)
            return None
        return response.content

    @property
    def item_logo_bytes(self) -> bytes:
        return self.get_image(self.item_logo)

    @property
    def item_cover_bytes(self) -> bytes:
        return self.get_image(self.item_cover)

    @property
    def pickupdate(self) -> str:
        """
        Returns a well formated string, providing the pickup time range
        """
        if self.pickup_interval_start and self.pickup_interval_end:
            now = datetime.datetime.now()
            pfr = self._datetimeparse(self.pickup_interval_start)
            pto = self._datetimeparse(self.pickup_interval_end)
            prange = (f"{pfr.hour:02d}:{pfr.minute:02d} - "
                      f"{pto.hour:02d}:{pto.minute:02d}")
            tommorow = now + datetime.timedelta(days=1)
            if now.date() == pfr.date():
                return f"{humanize.naturalday(now)}, {prange}"
            if (pfr.date() - now.date()).days == 1:
                return f"{humanize.naturalday(tommorow)}, {prange}"
            return f"{pfr.day}/{pfr.month}, {prange}"
        return "-"
