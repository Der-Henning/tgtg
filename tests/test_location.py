from pytest_mock.plugin import MockerFixture

from models import Location


def test_calculate_distance_time(mocker: MockerFixture):
    google_api_key = "AIza123456"
    location = "Hauptstraße 1, 20099 Hamburg, Germany"

    mocker.patch('googlemaps.Client.geocode', return_value=[{}])
    mocker.patch('googlemaps.Client.directions', return_value=[{
        "legs": [{
            "distance": {"value": 1500},
            "duration": {"value": 1200}
        }]
    }])

    distance_time_calculator = Location(
        True, google_api_key, location)
    distance_time = distance_time_calculator.calculate_distance_time(
        "München", Location.WALKING_MODE)

    assert distance_time.distance == 1500
    assert distance_time.duration == 1200
    assert distance_time.travel_mode == Location.WALKING_MODE
