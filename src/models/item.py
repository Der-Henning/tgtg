class Item():
    def __init__(self, data):
        self.id = data["item"]["item_id"]
        self.items_available = data["items_available"]
        self.display_name = data["display_name"]