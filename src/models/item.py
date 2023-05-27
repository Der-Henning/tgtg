import datetime
import logging
import re
from http import HTTPStatus

import humanize
import requests

from models import DistanceTimeCalculator
from models.errors import MaskConfigurationError

ATTRS = ["item_id", "items_available", "display_name", "description",
         "price", "currency", "pickupdate", "favorite", "rating",
         "buffet", "item_category", "item_name", "packaging_option",
         "pickup_location", "store_name", "item_logo", "item_cover",
         "scanned_on", "item_logo_bytes", "item_cover_bytes", "link",
         "walking_dt", "biking_dt", "driving_dt", "transit_dt"]

log = logging.getLogger('tgtg')


class Item():
    """
    Takes the raw data from the TGTG API and
    returns well formated data for notifications.
    """

    def __init__(self, data: dict, dt_calculator: DistanceTimeCalculator):
        self.items_available = data.get("items_available", 0)
        self.display_name = data.get("display_name", "-")
        self.favorite = "Yes" if data.get("favorite", False) else "No"
        self.pickup_interval_start = data.get(
            "pickup_interval", {}).get("start", None)
        self.pickup_interval_end = data.get(
            "pickup_interval", {}).get("end", None)
        self.pickup_location = data.get("pickup_location", {}).get(
            "address", {}).get("address_line", "-")

        item = data.get("item", {})
        self.item_id = item.get("item_id")
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
        self.dt_calculator = dt_calculator

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
    def link(self) -> str:
        return f"https://share.toogoodtogo.com/item/{self.item_id}"

    def unmask(self, text: str) -> str:
        """
        Replaces variables with the current values.
        """
        if text in ["${{item_logo_bytes}}", "${{item_cover_bytes}}"]:
            matches = re.findall(r"\${{([a-zA-Z0-9_]+)}}", text)
            return getattr(self, matches[0])
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", text):
            if hasattr(self, match.group(1)):
                val = getattr(self, match.group(1))
                text = text.replace(match.group(0), str(val))
        return text

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

    def get_distance_time(self, mode):
        return self.dt_calculator.calculate_distance_time(
            self.pickup_location, mode, self.item_id)

    @property
    def walking_dt(self):
        return self.get_distance_time('walking')

    @property
    def driving_dt(self):
        return self.get_distance_time('driving')

    @property
    def transit_dt(self):
        return self.get_distance_time('transit')

    @property
    def biking_dt(self):
        return self.get_distance_time('bicycling')
