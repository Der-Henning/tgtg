from pytest_mock.plugin import MockerFixture

from models import Location


def test_calculate_distance_time(mocker: MockerFixture):
    google_api_key = "AIza123456"
    destination = "Hauptstraße 1, 20099 Hamburg, Germany"

    mocker.patch('googlemaps.Client.geocode', return_value=[{}])
    mocker.patch('googlemaps.Client.directions', return_value=[{
        "legs": [{
            "distance": {"value": 1500},
            "duration": {"value": 1200}
        }]
    }])
    mocker.patch('googlemaps.Client.distance_matrix', return_value={
        "rows": [{
            "elements": [{
                "distance": {"value": 1500},
                "duration_in_traffic": {"value": 1400}
            }]
        }]
    })

    location = Location(True, google_api_key, destination)

    # Test case 1: Calculate distance/time without traffic
    distance_time = location.calculate_distance_time(
        "München", Location.DRIVING_MODE, traffic=False)
    assert distance_time.distance == 1500
    assert distance_time.duration == 1200
    assert distance_time.travel_mode == Location.DRIVING_MODE

    # Test case 2: Calculate distance/time with traffic
    distance_time = location.calculate_distance_time(
        "München", Location.DRIVING_MODE, traffic=True)
    assert distance_time.distance == 1500
    assert distance_time.duration == 1400
    assert distance_time.travel_mode == Location.DRIVING_MODE
