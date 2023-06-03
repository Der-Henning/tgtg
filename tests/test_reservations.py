from unittest.mock import MagicMock

import pytest

from models.item import Item
from models.reservations import Order, Reservation, Reservations


@pytest.fixture
def reservations():
    mock_client = MagicMock()
    mock_client.get_order_status.return_value = {"state": "RESERVED"}
    return Reservations(mock_client)


def test_reserve(reservations: Reservations):
    reservations.reserve("123", "Test Item")
    assert len(reservations.reservation_query) == 1


def test_make_orders(reservations: Reservations, tgtg_item: dict):
    callback_mock = MagicMock()
    reservations.reserve("123", "Test Item")
    reservations.make_orders({"123": Item(tgtg_item)}, callback_mock)
    assert len(reservations.active_orders) == 1
    assert len(reservations.reservation_query) == 0
    callback_mock.assert_called_once_with(
        Reservation("123", 1, "Test Item")
    )


def test_update_active_orders(reservations: Reservations):
    order = Order("1", "123", 1, "Test Item")
    reservations.active_orders = [order]
    reservations.update_active_orders()
    assert len(reservations.active_orders) == 1
    reservations.client.get_order_status.return_value = {"state": "CANELLED"}
    reservations.update_active_orders()
    assert len(reservations.active_orders) == 0


def test_cancel_order(reservations: Reservations):
    order = Order("1", "123", 1, "Test Item")
    reservations.active_orders = [order]
    reservations.cancel_order(order)


def test_cancel_all_orders(reservations: Reservations):
    order1 = Order("1", "123", 1, "Test Item 1")
    order2 = Order("2", "123", 2, "Test Item 2")
    reservations.active_orders = [order1, order2]
    reservations.cancel_all_orders()


def test_get_favorites(reservations: Reservations, tgtg_item: dict):
    reservations.client.get_favorites.return_value = [tgtg_item]
    favorites = reservations.get_favorites()
    assert len(favorites) == 1
    assert favorites[0].item_id == tgtg_item.get("item", {}).get("item_id")
    assert favorites[0].display_name == tgtg_item.get("display_name")
    assert favorites[0].items_available == tgtg_item.get("items_available")


def test_create_order(reservations: Reservations):
    reservations.client.create_order.return_value = {"id": "1"}
    reservation = Reservation("123", 1, "Test Item")
    reservations._create_order(reservation)
    assert len(reservations.active_orders) == 1
    assert len(reservations.reservation_query) == 0
    assert reservations.active_orders[0].id == "1"
    assert reservations.active_orders[0].item_id == "123"
    assert reservations.active_orders[0].amount == 1
    assert reservations.active_orders[0].display_name == "Test Item"
