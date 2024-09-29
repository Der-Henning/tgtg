import datetime
import logging
import re
from http import HTTPStatus
from typing import Any, Union

import babel.numbers
import humanize
import requests

from tgtg_scanner.errors import MaskConfigurationError
from tgtg_scanner.models.location import DistanceTime, Location

ATTRS = [
    "item_id",
    "items_available",
    "display_name",
    "description",
    "price",
    "value",
    "currency",
    "pickupdate",
    "favorite",
    "rating",
    "buffet",
    "item_category",
    "item_name",
    "packaging_option",
    "pickup_location",
    "store_name",
    "item_logo",
    "item_cover",
    "scanned_on",
    "item_logo_bytes",
    "item_cover_bytes",
    "link",
    "distance_walking",
    "distance_driving",
    "distance_transit",
    "distance_biking",
    "duration_walking",
    "duration_driving",
    "duration_transit",
    "duration_biking",
]

log = logging.getLogger("tgtg")


class Item:
    """
    Takes the raw data from the TGTG API and
    returns well formated data for notifications.
    """

    def __init__(self, data: dict, location: Union[Location, None] = None, locale: str = "en_US"):
        self.items_available: int = data.get("items_available", 0)
        self.display_name: str = data.get("display_name", "-")
        self.favorite: str = "Yes" if data.get("favorite", False) else "No"
        self.pickup_interval_start: Union[str, None] = data.get("pickup_interval", {}).get("start", None)
        self.pickup_interval_end: Union[str, None] = data.get("pickup_interval", {}).get("end", None)
        self.pickup_location: str = data.get("pickup_location", {}).get("address", {}).get("address_line", "-")

        item: dict = data.get("item", {})
        self.item_id: str = item.get("item_id", None)
        self._rating: Union[float, None] = item.get("average_overall_rating", {}).get("average_overall_rating", None)
        self.packaging_option: str = item.get("packaging_option", "-")
        self.item_name: str = item.get("name", "-")
        self.buffet: str = "Yes" if item.get("buffet", False) else "No"
        self.item_category: str = item.get("item_category", "-")
        self.description: str = item.get("description", "-")
        item_price: dict = item.get("item_price", {})
        item_value: dict = item.get("item_value", {})
        self._price: float = item_price.get("minor_units", 0) / 10 ** item_price.get("decimals", 0)
        self._value: float = item_value.get("minor_units", 0) / 10 ** item_value.get("decimals", 0)
        self.currency: str = item_price.get("code", "-")
        self.item_logo: str = item.get("logo_picture", {}).get(
            "current_url",
            "https://tgtg-mkt-cms-prod.s3.eu-west-1.amazonaws.com/13512/TGTG_Icon_White_Cirle_1988x1988px_RGB.png",
        )
        self.item_cover: str = item.get("cover_picture", {}).get(
            "current_url",
            "https://images.tgtg.ninja/standard_images/GENERAL/other1.jpg",
        )

        store: dict = data.get("store", {})
        self.store_name: str = store.get("store_name", "-")

        self.scanned_on: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.location = location
        self.locale = locale

    @property
    def rating(self) -> str:
        if self._rating is None:
            return "-"
        return self._format_decimal(round(self._rating, 1))

    @property
    def price(self) -> str:
        return self._format_currency(self._price)

    @property
    def value(self) -> str:
        return self._format_currency(self._value)

    def _format_decimal(self, number: float) -> str:
        return babel.numbers.format_decimal(number, locale=self.locale)

    def _format_currency(self, number: float) -> str:
        if self.currency == "-":
            return self._format_decimal(number)
        return babel.numbers.format_currency(number, self.currency, locale=self.locale)

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
    def get_image(url: str) -> Union[bytes, None]:
        response = requests.get(url)
        if not response.status_code == HTTPStatus.OK:
            log.warning("Get Image Error: %s - %s", response.status_code, response.content)
            return None
        return response.content

    @property
    def item_logo_bytes(self) -> Union[bytes, None]:
        return self.get_image(self.item_logo)

    @property
    def item_cover_bytes(self) -> Union[bytes, None]:
        return self.get_image(self.item_cover)

    @property
    def link(self) -> str:
        return f"https://share.toogoodtogo.com/item/{self.item_id}"

    def _get_variables(self, text: str) -> list[re.Match]:
        """
        Returns a list of all variables in the provided string
        """
        return list(re.finditer(r"\${{([a-zA-Z0-9_]+)}}", text))

    def unmask(self, text: str) -> str:
        """
        Replaces variables with the current values.
        """
        if text in ["${{item_logo_bytes}}", "${{item_cover_bytes}}"]:
            matches = self._get_variables(text)
            return getattr(self, matches[0].group(1))
        for match in self._get_variables(text):
            if hasattr(self, match.group(1)):
                val = getattr(self, match.group(1))
                text = text.replace(match.group(0), str(val))
        return text

    @property
    def pickupdate(self) -> str:
        """
        Returns a well formated string, providing the pickup time range
        """
        if self.pickup_interval_start is None or self.pickup_interval_end is None:
            return "-"
        now = datetime.datetime.now()
        pfr = self._datetimeparse(self.pickup_interval_start)
        pto = self._datetimeparse(self.pickup_interval_end)
        prange = f"{pfr.hour:02d}:{pfr.minute:02d} - {pto.hour:02d}:{pto.minute:02d}"
        tommorow = now + datetime.timedelta(days=1)
        if now.date() == pfr.date():
            return f"{humanize.naturalday(now)}, {prange}"
        if (pfr.date() - now.date()).days == 1:
            return f"{humanize.naturalday(tommorow)}, {prange}"
        return f"{pfr.day}/{pfr.month}, {prange}"

    def _get_distance_time(self, travel_mode: str) -> Union[DistanceTime, None]:
        if self.location is None:
            return None
        return self.location.calculate_distance_time(self.pickup_location, travel_mode)

    def _get_distance(self, travel_mode: str) -> str:
        distance_time = self._get_distance_time(travel_mode)
        if distance_time is None:
            return "n/a"
        return f"{distance_time.distance / 1000:.1f} km"

    def _get_duration(self, travel_mode: str) -> str:
        distance_time = self._get_distance_time(travel_mode)
        if distance_time is None:
            return "n/a"
        return humanize.precisedelta(
            datetime.timedelta(seconds=distance_time.duration),
            minimum_unit="minutes",
            format="%0.0f",
        )

    def __getattribute__(self, __name: str) -> Any:
        try:
            return super().__getattribute__(__name)
        except AttributeError:
            if __name in ATTRS and __name.startswith(("distance", "duration")):
                _type, _mode = __name.split("_")
                if _type == "distance":
                    return self._get_distance(_mode)
                if _type == "duration":
                    return self._get_duration(_mode)
            raise
