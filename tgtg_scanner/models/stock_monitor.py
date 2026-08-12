"""Detect stock / price changes between scan cycles."""

from __future__ import annotations

import logging

from tgtg_scanner.models.item import Item

log = logging.getLogger("tgtg")


class StockMonitor:
    """Tracks previous item snapshots and decides when to notify."""

    def __init__(self, *, price_monitoring: bool = False) -> None:
        self.price_monitoring = price_monitoring
        self.state: dict[str, Item] = {}

    def observe(self, item: Item) -> bool:
        """Update state for ``item``. Return True if a notification should be sent."""
        previous = self.state.get(item.item_id)
        notify = False

        if previous is not None:
            item._previous_price = previous._price
            if previous.items_available != item.items_available:
                log.info(
                    "%s - amount changed from %s to %s",
                    item.display_name,
                    previous.items_available,
                    item.items_available,
                )
                if previous.items_available == 0 and item.items_available > 0:
                    notify = True
            if previous.price != item.price:
                log.info(
                    "%s - price changed from %s to %s",
                    item.display_name,
                    previous.price,
                    item.price,
                )
                if self.price_monitoring and item.items_available > 0 and item._price < previous._price:
                    notify = True

        self.state[item.item_id] = item
        return notify
