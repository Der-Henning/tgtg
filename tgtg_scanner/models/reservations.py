import logging
from dataclasses import dataclass
from typing import Callable

from tgtg_scanner.models.item import Item
from tgtg_scanner.tgtg import TgtgClient

log = logging.getLogger("tgtg")


@dataclass
class Order:
    id: str
    item_id: str
    amount: int
    display_name: str


@dataclass
class Reservation:
    item_id: str
    amount: int
    display_name: str


class Reservations:
    def __init__(self, client: TgtgClient) -> None:
        self.client = client
        self.reservation_query: list[Reservation] = []
        self.active_orders: dict[str, Order] = {}

    def reserve(self, item_id: str, display_name: str, amount: int = 1) -> None:
        """Create a new reservation.

        Args:
            item_id (str): Item ID
            display_name (str): Item display name
            amount (int, optional): Amount. Defaults to 1.

        """
        self.reservation_query.append(Reservation(item_id, amount, display_name))

    def make_orders(self, state: dict[str, Item], callback: Callable[[Reservation], None]) -> None:
        """Create orders for reservations.

        Args:
            state (Dict[str, Item]): Current item state
            callback (Callable[[Reservation], None]): Callback for each order

        """
        for reservation in self.reservation_query:
            item = state.get(reservation.item_id)
            if item and item.items_available > 0:
                try:
                    self._create_order(reservation)
                    self.reservation_query.remove(reservation)
                    callback(reservation)
                except Exception as exc:
                    log.warning("Order failed: %s", exc)

    def update_active_orders(self) -> None:
        """Remove orders that are not active anymore."""
        for order_id in list(self.active_orders):
            res = self.client.get_order_status(order_id)
            if res.get("state") != "RESERVED":
                del self.active_orders[order_id]

    def cancel_order(self, order_id: str) -> None:
        """Cancel an order."""
        self.client.abort_order(order_id)

    def cancel_all_orders(self) -> None:
        """Cancel all active orders."""
        for order_id in list(self.active_orders):
            self.cancel_order(order_id)

    def _create_order(self, reservation: Reservation) -> None:
        res = self.client.create_order(reservation.item_id, reservation.amount)
        order_id = res.get("id")
        if order_id:
            order = Order(
                order_id,
                reservation.item_id,
                reservation.amount,
                reservation.display_name,
            )
            self.active_orders[order_id] = order
