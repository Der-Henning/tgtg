import logging

from prometheus_client import Counter, Gauge, start_http_server

from tgtg_scanner.models.item import Item

log = logging.getLogger("tgtg")


class Metrics:
    """
    Provides a prometheus metrics client.
    """

    def __init__(self, port: int = 8000):
        self.port = port
        self.item_count = Gauge("tgtg_item_count", "Currently available Magic Bags", ["item_id", "display_name"])
        self.item_price = Gauge("tgtg_item_price", "Price for a Magic Bag", ["item_id", "display_name"])
        self.item_value = Gauge("tgtg_item_value", "Value for a Magic Bag", ["item_id", "display_name"])
        self.get_favorites_errors = Counter(
            "tgtg_get_favorites_errors",
            "Count of request errors fetching tgtg favorites",
        )
        self.send_notifications = Counter(
            "tgtg_send_notifications",
            "Count of send notifications",
            ["item_id", "display_name"],
        )

    def enable_metrics(self) -> None:
        """
        Start the metrics http server.
        """
        start_http_server(self.port)
        log.info("Metrics server startet on port %s", self.port)

    def update(self, item: Item) -> None:
        """
        Update the metrics.
        """
        try:
            self.item_count.labels(item.item_id, item.display_name).set(item.items_available)
            self.item_price.labels(item.item_id, item.display_name).set(item._price)
            self.item_value.labels(item.item_id, item.display_name).set(item._value)
        except ValueError as err:
            log.warning("Error updating metrics: %s", err)
