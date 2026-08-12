from tgtg_scanner.models.item import Item
from tgtg_scanner.models.stock_monitor import StockMonitor


def _item(item_id: str, available: int, price_minor: int = 499) -> Item:
    return Item(
        {
            "items_available": available,
            "display_name": f"Shop {item_id}",
            "favorite": True,
            "item": {
                "item_id": item_id,
                "item_price": {"code": "EUR", "minor_units": price_minor, "decimals": 2},
                "item_value": {"code": "EUR", "minor_units": 1500, "decimals": 2},
            },
            "store": {"store_name": "Shop"},
        }
    )


def test_no_notify_on_first_sight():
    monitor = StockMonitor()
    assert monitor.observe(_item("1", 2)) is False
    assert monitor.state["1"].items_available == 2


def test_notify_on_stock_available():
    monitor = StockMonitor()
    monitor.observe(_item("1", 0))
    assert monitor.observe(_item("1", 3)) is True


def test_no_notify_when_already_in_stock():
    monitor = StockMonitor()
    monitor.observe(_item("1", 2))
    assert monitor.observe(_item("1", 5)) is False


def test_notify_on_price_drop():
    monitor = StockMonitor(price_monitoring=True)
    monitor.observe(_item("1", 1, price_minor=500))
    assert monitor.observe(_item("1", 1, price_minor=400)) is True


def test_price_drop_ignored_without_flag():
    monitor = StockMonitor(price_monitoring=False)
    monitor.observe(_item("1", 1, price_minor=500))
    assert monitor.observe(_item("1", 1, price_minor=400)) is False
