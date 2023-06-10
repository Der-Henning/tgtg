import datetime
import re
from typing import Any, Union

import humanize

from models.errors import MaskConfigurationError
from models.location import DistanceTime, Location

COMMON_ATTRS = [
    "item_id", "packaging_option", "pickup_location", "store_name",
    "distance_walking", "distance_driving", "distance_transit",
    "distance_bicycling", "duration_walking", "duration_driving",
    "duration_transit", "duration_bicycling"
]


class Order_Item_Base:
    ATTRS = COMMON_ATTRS.copy()

    def __init__(self, data: dict, location: Location = None):
        self.is_order = None
        self.pickup_location = data.get("pickup_location", {}).get(
            "address", {}).get("address_line", "-")
        self.pickup_interval_start = data.get(
            "pickup_interval", {}).get("start", None)
        self.pickup_interval_end = data.get(
            "pickup_interval", {}).get("end", None)
        self.item_id = data.get("item_id")
        self.location = location

    @property
    def link(self) -> str:
        return f"https://share.toogoodtogo.com/item/{self.item_id}"

    @classmethod
    def check_mask(cls, text: str) -> None:
        """
        Checks whether the variables in the provided string are available

        Raises MaskConfigurationError
        """
        for match in re.finditer(r"\${{([a-zA-Z0-9_]+)}}", text):
            if not match.group(1) in cls.ATTRS:
                raise MaskConfigurationError(match.group(0))

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

    def _get_variables(self, text: str) -> list[re.Match]:
        """
        Returns a list of all variables in the provided string
        """
        return list(re.finditer(r"\${{([a-zA-Z0-9_]+)}}", text))

    def _get_distance(self, travel_mode: str) -> str:
        distance_time = self._get_distance_time(travel_mode)
        if distance_time is None:
            return 'n/a'
        return f"{distance_time.distance / 1000:.1f} km"

    def _get_duration(self, travel_mode: str) -> str:
        distance_time = self._get_distance_time(travel_mode)
        if distance_time is None:
            return 'n/a'
        return humanize.precisedelta(
            datetime.timedelta(seconds=distance_time.duration),
            minimum_unit="minutes", format="%0.0f")

    def _get_distance_time(self, travel_mode: str) -> Union[DistanceTime,
                                                            None]:
        if self.location is None:
            return None
        return self.location.calculate_distance_time(
            self.pickup_location, travel_mode, self.is_order)

    def __getattribute__(self, __name: str) -> Any:
        try:
            return super().__getattribute__(__name)
        except AttributeError:
            if __name in self.ATTRS and __name.startswith(("distance",
                                                           "duration")):
                _type, _mode = __name.split("_")
                if _type == "distance":
                    return self._get_distance(_mode)
                if _type == "duration":
                    return self._get_duration(_mode)
            raise
