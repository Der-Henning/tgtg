import pytest

from tgtg_scanner.models.item import Item


def test_item(tgtg_item: dict, monkeypatch: pytest.MonkeyPatch):
    item = Item(tgtg_item)
    assert item.item_id == tgtg_item.get("item", {}).get("item_id")
    assert item.display_name == tgtg_item.get("display_name")
    assert item.items_available == tgtg_item.get("items_available")
    assert item.favorite == "No"
    assert item.pickup_location == tgtg_item.get("pickup_location", {}).get("address", {}).get("address_line", "-")
    assert item.rating == "3.6"
    assert item.packaging_option == tgtg_item.get("item", {}).get("packaging_option", "-")
    assert item.item_name == tgtg_item.get("item", {}).get("name", "-")
    assert item.buffet == "No"
    assert item.item_category == tgtg_item.get("item", {}).get("item_category", "-")
    assert item.description == tgtg_item.get("item", {}).get("description", "-")
    assert item.link == "https://share.toogoodtogo.com/item/774625"
    assert item.price == "€3.00"
    assert item.value == "€9.00"
    assert item.currency == "EUR"
    assert item.store_name == tgtg_item.get("store", {}).get("store_name", "-")
    assert item.item_logo == tgtg_item.get("item", {}).get("logo_picture", {}).get("current_url", "-")
    assert item.item_cover == tgtg_item.get("item", {}).get("cover_picture", {}).get("current_url", "-")


def test_item_pickupdate_24h_format(tgtg_item: dict):
    """Test pickup date formatting with 24-hour time format."""
    item = Item(tgtg_item, time_format="24h")
    pickupdate = item.pickupdate
    # The pickup time should be formatted as 24-hour with colon separator (e.g., "19:00 - 19:30")
    # Check that it contains the colon format and doesn't contain AM/PM
    assert ":" in pickupdate
    assert " - " in pickupdate
    assert "AM" not in pickupdate
    assert "PM" not in pickupdate


def test_item_pickupdate_12h_format(tgtg_item: dict):
    """Test pickup date formatting with 12-hour time format."""
    item = Item(tgtg_item, time_format="12h")
    pickupdate = item.pickupdate
    # The pickup time should be formatted as 12-hour with AM/PM (e.g., "07:00 PM - 07:30 PM")
    assert "PM" in pickupdate or "AM" in pickupdate
    assert ":" in pickupdate
