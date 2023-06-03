import googlemaps
import logging
from models.errors import LocationConfigurationError
from shared_variables import DRIVING_MODE

log = logging.getLogger("tgtg")


class DistanceTimeCalculator:
    def __init__(self, enabled, api_key, origin):
        """
        Initializes DistanceTimeCalculator class.
        First run flag important only for validating origin address.
        """
        self.enabled = enabled
        if enabled:
            self.gmaps = googlemaps.Client(key=api_key)
        self.origin = origin
        self.is_first_run = True

        # cached DistanceTime object for each item_id+mode
        self.distancetime_dict: dict[str, str] = {}

        self.time_cache: dict[str, int] = {}
        self.distance_cache: dict[str, float] = {}

    def calculate_distance_time(self, destination, mode, item_id):
        """
        Returns formatted distance and time string.
        """
        if not self._is_valid_run(destination):
            return 'n/a'

        distance_in_km, time_in_minutes = self._calculate_distance_time(
            destination, mode, item_id)

        time = f"{time_in_minutes} min"
        distance = f"{distance_in_km} km"

        return f'{time} - {distance}'

    def _calculate_distance_time(self, destination, mode, item_id):
        """
        Calculates the distance and time taken to travel from
        origin to destination using the given mode of transportation.
        """
        key = f'{item_id}{mode}'

        # use cached value if available
        if key in self.time_cache and key in self.distance_cache:
            return self.distance_cache[key], self.time_cache[key]

        log.info(f"Sending Google Maps API request: {destination} using {mode} mode")

        # calculate distance and time
        directions = self.gmaps.directions(self.origin, destination, mode=mode)
        leg = directions[0]["legs"][0]
        distance_in_km = round(leg["distance"]["value"] / 1000, 2)
        time_in_minutes = int(round(leg["duration"]["value"] / 60, 0))

        # cache values
        self.time_cache[key] = time_in_minutes
        self.distance_cache[key] = distance_in_km

        return distance_in_km, time_in_minutes

    def calculate_time_with_traffic(self, destination, mode, item_id):
        """
        Calculates travel time from origin to destination using driving
        mode with traffic. All other modes use static time.
        Returns time in minutes.
        """
        if not self._is_valid_run(destination):
            return 'n/a'

        if mode == DRIVING_MODE:
            log.info(
                f"Sending Google Maps API (traffic) request: {destination}")

            # Calculate time with traffic
            directions = self.gmaps.directions(
                self.origin, destination, mode=mode,
                departure_time='now'
            )
            time_in_minutes = int(
                round(directions[0]["legs"][0]["duration"]["value"] / 60, 0)
            )
        else:
            # Calculate static time
            _, time_in_minutes = self._calculate_distance_time(
                destination, mode, item_id
            )

        return time_in_minutes

    def _is_valid_run(self, destination) -> bool:
        """
        Checks if the location config and destination config of item is valid.
        """
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
        """
        Checks if the given address is valid using
        the Google Maps Geocoding API.
        """
        try:
            self.gmaps.geocode(address)
        except Exception:
            log.error(f"Address not found: {address}")
            return False
        return True
