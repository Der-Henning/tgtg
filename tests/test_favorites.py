from unittest.mock import MagicMock, call

import pytest

from tgtg_scanner.errors import TgtgAPIError
from tgtg_scanner.models.favorites import Favorites


@pytest.fixture
def favorites():
    mock_client = MagicMock()
    return Favorites(mock_client)


def test_is_item_favorite(favorites: Favorites, tgtg_item: dict):
    favorites.client.get_favorites.return_value = []
    is_favorite = favorites.is_item_favorite(
        tgtg_item.get("item", {}).get("item_id"))
    assert is_favorite == tgtg_item.get("favorite")

    is_favorite = favorites.is_item_favorite("123")
    assert is_favorite is False


def test_get_item_by_id(favorites: Favorites, tgtg_item: dict):
    item_id = tgtg_item.get("item", {}).get("item_id")
    favorites.client.get_item.side_effect = lambda x: tgtg_item \
        if x == item_id else (_ for _ in ()).throw(TgtgAPIError())
    item = favorites.get_item_by_id(item_id)
    assert item.item_id == item_id
    assert item.display_name == tgtg_item.get("display_name")
    assert item.items_available == tgtg_item.get("items_available")

    item = favorites.get_item_by_id("123")
    assert not item.item_id
    assert item.display_name == "-"
    assert item.items_available == 0


def test_get_favorites(favorites: Favorites, tgtg_item: dict):
    favorites.client.get_favorites.return_value = [tgtg_item]
    favorites = favorites.get_favorites()
    assert len(favorites) == 1
    assert favorites[0].item_id == tgtg_item.get("item", {}).get("item_id")
    assert favorites[0].display_name == tgtg_item.get("display_name")
    assert favorites[0].items_available == tgtg_item.get("items_available")


def test_add_favorites(favorites: Favorites):
    set_favorite_mock = MagicMock()
    favorites.client.set_favorite = set_favorite_mock
    favorites.add_favorites(["123", "234"])
    set_favorite_mock.assert_has_calls([call("123", True), call("234", True)])


def test_remove_favorites(favorites: Favorites):
    set_favorite_mock = MagicMock()
    favorites.client.set_favorite = set_favorite_mock
    favorites.remove_favorite(["123", "234"])
    set_favorite_mock.assert_has_calls(
        [call("123", False), call("234", False)])
