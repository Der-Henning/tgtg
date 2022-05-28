import sys
import getopt
import json
import logging
from scanner import Scanner

log = logging.getLogger('tgtg')
log.setLevel(logging.INFO)


class Helper(Scanner):

    @property
    def credentials(self):
        return self.tgtg_client.get_credentials()

    # returns item_ids for given latitude, longitude and radius
    def get_items(self, lat, lng, radius):
        return self.tgtg_client.get_items(
            favorites_only=False,
            latitude=lat,
            longitude=lng,
            radius=radius,
        )

    # returns all favorites of given tgtg account
    @property
    def favorites(self):
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
                log.error("getItem Error! - %s", sys.exc_info())
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
        for item_id in item_ids:
            self.unset_favorite(item_id)


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "h", ["help"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    for opt, _ in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
    if len(args) < 1:
        usage()
        sys.exit(2)

    helper = Helper(notifiers=False)

    if len(args) == 1 and args[0] == "credentials":
        credentials = helper.credentials
        print("")
        print("TGTG credentials:")
        print("Access Token: ", credentials["access_token"])
        print("Refresh Token:", credentials["refresh_token"])
        print("User ID:      ", credentials["user_id"])
        print("")
    elif len(args) == 1 and args[0] == "favorites":
        favorites = helper.favorites
        print("")
        print("My Favorites:")
        print(json.dumps(favorites, sort_keys=True, indent=4))
        print("")
    elif len(args) == 2 and args[0] == "delete":
        if args[1] == "all":
            if input("Delete all your favorites? [y/n]") == "y":
                helper.remove_all_favorites()
        else:
            if input(f"Delete {args[1]} form your favorites? [y/n]") == "y":
                helper.unset_favorite(args[1])
    elif len(args) == 2 and args[0] == "add":
        helper.set_favorite(args[1])
    elif len(args) == 4 and args[0] == "find":
        items = helper.get_items(args[1], args[2], args[3])
        print("")
        print(json.dumps(items, sort_keys=True, indent=4))
    else:
        usage()
        sys.exit()


def usage():
    print("Usage: helper.py command")
    print("  commands:")
    print("  - credentials:            displays your TGTG tokens")
    print("  - favorites:              displays your favorite magic bags data")
    print("  - find [lat] [lng] [rad]: displays items for position and radius")
    print("  - add [item_id]:          adds [item_id] to your favorites")
    print("  - delete all:             removes all your favorites")
    print("  - delete [item_id]:       removes [item_id] from your favorites")


if __name__ == "__main__":
    main(sys.argv[1:])
