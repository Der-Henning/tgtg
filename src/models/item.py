class Item():
    ATTRS = ["item_id", "items_available", "display_name"]

    def __init__(self, data):
        self.item_id = data["item"]["item_id"]
        self.items_available = data["items_available"]
        self.display_name = data["display_name"]
