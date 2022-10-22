from typing import List
import logging

from models import Config
from scanner import Scanner

log = logging.getLogger("tgtg")


class Helper(Scanner):
    def __init__(self, config: Config):
        super().__init__(config, disable_notifiers=True)

    def get_credentials(self) -> dict:
        """Returns current tgtg credentials.

        Returns:
            dict: dictionary containing access token, refresh token and user id
        """
        return self.tgtg_client.get_credentials()

    def get_items(self, lat, lng, radius) -> List[dict]:
        """Get items by geographic position.

        Args:
            lat (float): latitude
            lng (float): longitude
            radius (int): radius in meter

        Returns:
            List: List of found items
        """
        return self.tgtg_client.get_items(
            favorites_only=False,
            latitude=lat,
            longitude=lng,
            radius=radius,
        )

    def get_favorites(self) -> List[dict]:
        """Returns favorites of the current tgtg account

        Returns:
            List: List of items
        """
        items = []
        page = 1
        page_size = 100
        while True:
            new_items = self.tgtg_client.get_items(
                favorites_only=True,
                page_size=page_size,
                page=page
            )
            items += new_items
            if len(new_items) < page_size:
                break
            page += 1
        return items

    def set_favorite(self, item_id: str) -> None:
        """Add item to favorites.

        Args:
            item_id (str): Item ID
        """
        self.tgtg_client.set_favorite(item_id=item_id, is_favorite=True)

    def unset_favorite(self, item_id: str) -> None:
        """Remove item from favorites.

        Args:
            item_id (str): Item ID
        """
        self.tgtg_client.set_favorite(item_id=item_id, is_favorite=False)

    def unset_all_favorites(self) -> None:
        """Remove all items from favorites."""
        item_ids = [item["item"]["item_id"] for item in self.get_favorites()]
        for item_id in item_ids:
            self.unset_favorite(item_id)
