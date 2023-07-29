from unittest.mock import MagicMock

import pytest

from tgtg_scanner.models.item import Item
from tgtg_scanner.models.reservations import Order, Reservation, Reservations


@pytest.fixture(scope="function")
def reservations():
    mock_client = MagicMock()
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
        Reservation("123", 1, "Test Item"))


def test_update_active_orders(reservations: Reservations):
    order = Order("1", "123", 1, "Test Item")
    reservations.client.get_order_status.return_value = {"state": "RESERVED"}
    reservations.active_orders = {order.id: order}
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
