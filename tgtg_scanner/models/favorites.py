import logging
from dataclasses import dataclass
from typing import List

from tgtg_scanner.errors import TgtgAPIError
from tgtg_scanner.models.item import Item
from tgtg_scanner.tgtg import TgtgClient

log = logging.getLogger("tgtg")


@dataclass
class AddFavoriteRequest():
    item_id: str
    item_display_name: str
    proceed: bool


@dataclass
class RemoveFavoriteRequest():
    item_id: str
    item_display_name: str
    proceed: bool


class Favorites():
    def __init__(self, client: TgtgClient) -> None:
        self.client = client

    def is_item_favorite(self, item_id: str) -> bool:
        """Returns true if the provided item ID is in the favorites

        Args:
            item_id (str): Item ID
        Returns:
            bool: true, if the provided item ID is in the favorites
        """
        return any(item for item
                   in self.client.get_favorites()
                   if Item(item).item_id == item_id)

    def get_item_by_id(self, item_id: str) -> Item:
        """Gets an item by the Item ID

        Args:
            item_id (str): Item ID
        Returns:
            Item: the Item for the Item ID or an empty Item
        """
        try:
            return Item(self.client.get_item(item_id))
        except TgtgAPIError:
            return Item({})

    def get_favorites(self) -> List[Item]:
        """Get all favorite items

        Return:
            List: List of favorite items
        """
        return [Item(item) for item in self.client.get_favorites()]

    def add_favorites(self, item_ids: List[str]) -> None:
        """Adds all the provided item IDs to the favorites

        Args:
            item_ids (str): Item ID list
        """
        for item_id in item_ids:
            self.client.set_favorite(item_id, True)

    def remove_favorite(self, item_ids: List[str]) -> None:
        """Removes all the provided item IDs from the favorites

        Args:
            item_ids (str): Item ID list
        """
        for item_id in item_ids:
            self.client.set_favorite(item_id, False)
