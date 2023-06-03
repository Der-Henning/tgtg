import logging
from dataclasses import dataclass
from typing import Union

import googlemaps

from models.errors import LocationConfigurationError

log = logging.getLogger("tgtg")


@dataclass
class DistanceTime:
    """
    Dataclass for distance and time.
    """
    distance: str
    duration: str
    travel_mode: str


class Location:
    WALKING_MODE = "walking"
    DRIVING_MODE = "driving"
    PUBLIC_TRANSPORT_MODE = "transit"
    BIKING_MODE = "bicycling"

    def __init__(self, enabled: bool, api_key: str, origin: str):
        """
        Initializes Location class.
        First run flag important only for validating origin address.
        """
        self.enabled = enabled
        self.origin = origin
        if enabled:
            if not api_key or not origin:
                raise LocationConfigurationError(
                    "Location enabled but no API key or origin address given")
            try:
                self.gmaps = googlemaps.Client(key=api_key)
            except ValueError as exc:
                raise LocationConfigurationError(exc) from exc
            if not self._is_address_valid(self.origin):
                raise LocationConfigurationError("Invalid origin address")

        # cached DistanceTime object for each item_id+mode
        self.distancetime_dict: dict[str, DistanceTime] = {}

    def calculate_distance_time(self, destination: str, travel_mode: str
                                ) -> Union[DistanceTime, None]:
        """
        Calculates the distance and time taken to travel from origin to
        destination using the given mode of transportation.
        Returns distance and time in km and minutes respectively.
        """
        if not self.enabled:
            log.debug("Location service disabled")
            return None

        if not self._is_address_valid(destination):
            return None

        key = f'{destination}_{travel_mode}'

        # use cached value if available
        if key in self.distancetime_dict:
            return self.distancetime_dict[key]

        log.debug(f"Sending Google Maps API request: "
                  f"{destination} using {travel_mode} mode")

        # calculate distance and time
        directions = self.gmaps.directions(self.origin, destination,
                                           mode=travel_mode)
        distance_time = DistanceTime(
            directions[0]["legs"][0]["distance"]["value"],
            directions[0]["legs"][0]["duration"]["value"],
            travel_mode)

        # cache value
        self.distancetime_dict[key] = distance_time

        return distance_time

    def _is_address_valid(self, address: str) -> bool:
        """
        Checks if the given address is valid using the
        Google Maps Geocoding API.
        """
        if len(self.gmaps.geocode(address)) == 0:
            log.debug(f"Invalid address: {address}")
            return False
        return True
