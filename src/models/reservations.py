from dataclasses import dataclass
from typing import Callable, Dict, List

from models.item import Item
from tgtg import TgtgClient


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
        self.reservation_query.append(
            Reservation(item_id, amount, display_name))

    def _create_order(self, reservation: Reservation) -> None:
        res = self.client.create_order(reservation.item_id, reservation.amount)
        order_id = res.get("id")
        order = Order(order_id,
                      reservation.item_id,
                      reservation.amount,
                      reservation.display_name)
        self.active_orders.append(order)
        self.reservation_query.remove(reservation)

    def make_orders(self, state: Dict[str, Item],
                    callback: Callable[[Reservation], None]) -> None:
        for reservation in self.reservation_query:
            if state.get(reservation.item_id).items_available > 0:
                self._create_order(reservation)
                callback(reservation)

    def update_active_orders(self) -> None:
        for order in self.active_orders:
            res = self.client.get_order_status(order.id)
            if res.get("state") != "RESERVED":
                self.active_orders.remove(order)

    def cancel_order(self, order: Order) -> None:
        self.client.abort_order(order.id)

    def cancel_all_orders(self) -> None:
        for order in self.active_orders:
            self.cancel_order(order)

    def get_favorites(self) -> List[Item]:
        return [Item(item) for item in self.client.get_favorites()]
