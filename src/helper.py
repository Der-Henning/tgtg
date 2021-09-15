from scanner import Scanner
from os import path
import sys
import logging as log


class Helper(Scanner):

    # returns item_ids for given latitude, longitude and radius
    def get_items(self, lat, lng, radius):
        return self.tgtg_client.get_items(
            favorites_only=False,
            latitude=lat,
            longitude=lng,
            radius=radius,
        )

    # returns all favorites of given tgtg account
    def get_favorites(self):
        items = []
        page = 1
        page_size = 100
        while True:
            try:
                new_items = self.tgtg_client.get_items(
                    favorites_only=True,
                    page_size=page_size,
                    page=page
                )
                items += new_items
                if len(new_items) < page_size:
                    break
            except:
                log.error("getItem Error! - {0}".format(sys.exc_info()))
            finally:
                page += 1
        return items

    # adds item_id to tgtg account favorites
    def set_favorite(self, item_id):
        self.tgtg_client.set_favorite(item_id=item_id, is_favorite=True)

    # removes item_id from tgtg account favorites
    def unset_favorite(self, item_id):
        self.tgtg_client.set_favorite(item_id=item_id, is_favorite=False)

    # removes all favorites from given tgtg account
    def remove_all_favorites(self):
        item_ids = [item["item"]["item_id"] for item in self.get_favorites()]
        print(item_ids)
        for item_id in item_ids:
            self.unset_favorite(item_id)
