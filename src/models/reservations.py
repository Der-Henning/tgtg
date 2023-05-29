import logging
from dataclasses import dataclass
from typing import Callable, Dict, List

from models.item import Item
from tgtg import TgtgClient

log = logging.getLogger("tgtg")


@dataclass
class Order():
    id: str
    item_id: str
    amount: int
    display_name: str


@dataclass
class Reservation():
    item_id: str
    amount: int
    display_name: str


class Reservations():
    def __init__(self, client: TgtgClient) -> None:
        self.client = client
        self.reservation_query: List[Reservation] = []
        self.active_orders: List[Order] = []

    def reserve(self, item_id: str,
                display_name: str,
                amount: int = 1) -> None:
        """Create a new reservation

        Args:
            item_id (str): Item ID
            display_name (str): Item display name
            amount (int, optional): Amount. Defaults to 1.
        """
        self.reservation_query.append(
            Reservation(item_id, amount, display_name))

    def make_orders(self, state: Dict[str, Item],
                    callback: Callable[[Reservation], None]) -> None:
        """Create orders for reservations

        Args:
            state (Dict[str, Item]): Current item state
            callback (Callable[[Reservation], None]): Callback for each order
        """
        for reservation in self.reservation_query:
            if state.get(reservation.item_id).items_available > 0:
                self._create_order(reservation)
                callback(reservation)

    def update_active_orders(self) -> None:
        """Remove orders that are not active anymore
        """
        for order in self.active_orders:
            res = self.client.get_order_status(order.id)
            if res.get("state") != "RESERVED":
                self.active_orders.remove(order)

    def cancel_order(self, order: Order) -> None:
        """Cancel an order
        """
        self.client.abort_order(order.id)

    def cancel_all_orders(self) -> None:
        """Cancel all active orders
        """
        for order in self.active_orders:
            self.cancel_order(order)

    def get_favorites(self) -> List[Item]:
        """Get all favorite items
        """
        return [Item(item) for item in self.client.get_favorites()]

    def _create_order(self, reservation: Reservation) -> None:
        try:
            res = self.client.create_order(
                reservation.item_id, reservation.amount)
            order_id = res.get("id")
            order = Order(order_id,
                          reservation.item_id,
                          reservation.amount,
                          reservation.display_name)
            self.active_orders.append(order)
            self.reservation_query.remove(reservation)
        except Exception as exc:
            log.error("Create Order Error: %s", exc)
