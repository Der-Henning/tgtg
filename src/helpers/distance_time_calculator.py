import googlemaps
import requests
import json
import datetime
import logging
from models import DistanceTime
from models.errors import LocationConfigurationError

log = logging.getLogger("tgtg")


class DistanceTimeCalculator:
    WALKING_MODE = "walking"
    DRIVING_MODE = "driving"
    PUBLIC_TRANSPORT_MODE = "transit"

    def __init__(self, enabled, api_key, origin):
        self.enabled = enabled
        self.gmaps = googlemaps.Client(key=api_key)
        self.origin = origin
        self.is_first_run = True

    def _calculate_distance_time(self, destination, mode):
        directions = self.gmaps.directions(self.origin, destination, mode=mode)
        distance_in_km = round(
            directions[0]['legs'][0]['distance']['value'] / 1000, 2)
        distance = f'{distance_in_km} km'
        time_in_minutes = int(round(
            directions[0]['legs'][0]['duration']['value'] / 60, 0))
        time = f'{time_in_minutes} min'
        return distance, time

    def _is_valid_run(self, destination) -> bool:
        if not self.enabled:
            return False

        if self.is_first_run:
            self.is_first_run = False
            if not self._is_address_valid(self.origin):
                raise LocationConfigurationError()

        if not self._is_address_valid(destination):
            return False

        return True

    def _is_address_valid(self, address) -> bool:
        results = self.gmaps.geocode(address)
        if not results:
            log.error(f"Address not found: {address}")
            return False
        return True

    def calculate(self, destination) -> DistanceTime:
        if not self._is_valid_run(destination):
            return DistanceTime(0, 0, 0, 0, 0, 0)

        walking_distance, walking_time = self._calculate_distance_time(
            destination, self.WALKING_MODE)
        driving_distance, driving_time = self._calculate_distance_time(
            destination, self.DRIVING_MODE)
        transit_distance, transit_time = self._calculate_distance_time(
            destination, self.PUBLIC_TRANSPORT_MODE)
        return DistanceTime(
            walking_distance, walking_time, driving_distance, driving_time, transit_distance, transit_time
        )
