import requests
import json
import datetime
import logging

log = logging.getLogger("tgtg")


class DistanceTimeCalculator:
    def __init__(self, api_key, origin):
        self.api_key = api_key
        self.origin = origin

    def calculate_walking_distance_and_time(self, destination):
        # Send a GET request to the Directions API with mode=walking
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={self.origin}&destination={destination}&mode=walking&key={self.api_key}"
        response = requests.get(url)

        # Parse the JSON response
        data = json.loads(response.text)

        # Extract the walking distance and time in seconds
        distance = data["routes"][0]["legs"][0]["distance"]["value"]
        time = data["routes"][0]["legs"][0]["duration"]["value"]

        # Convert the walking time to a datetime object and return the distance and time
        walking_time = datetime.timedelta(seconds=time)
        log.info("Walking time: %s", walking_time)
        log.info("Walking distance: %s", distance / 1000)
        return distance, walking_time

    def calculate_driving_distance_and_time(self, destination):
        # Send a GET request to the Directions API with mode=driving
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={self.origin}&destination={destination}&mode=driving&key={self.api_key}"
        response = requests.get(url)

        # Parse the JSON response
        data = json.loads(response.text)

        # Extract the driving distance and time in seconds
        distance = data["routes"][0]["legs"][0]["distance"]["value"]
        time = data["routes"][0]["legs"][0]["duration"]["value"]

        # Convert the driving time to a datetime object and return the distance and time
        driving_time = datetime.timedelta(seconds=time)
        log.info("Driving time: %s", driving_time)
        log.info("Driving distance: %s", distance / 1000)
        return distance, driving_time
