import datetime


class Item():
    ATTRS = ["item_id", "items_available", "display_name",
             "price", "currency", "pickupdate"]

    def __init__(self, data):
        self.item_id = data["item"]["item_id"]
        self.items_available = data["items_available"]
        self.display_name = data["display_name"]
        self.price = 0
        self.currency = ""
        if 'price_including_taxes' in data["item"]:
            self.price = data["item"]["price_including_taxes"]["minor_units"] / \
                (10**data["item"]["price_including_taxes"]["decimals"])
            self.currency = data["item"]["price_including_taxes"]["code"]
        if 'pickup_interval' in data:
            self.interval_start = data['pickup_interval']['start']
            self.interval_end = data['pickup_interval']['end']

    @staticmethod
    def _datetimeparse(datestr):
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        value = datetime.datetime.strptime(datestr, fmt)
        return value.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

    @property
    def pickupdate(self):
        if (hasattr(self, "interval_start") and hasattr(self, "interval_end")):
            now = datetime.datetime.now()
            pfrom = self._datetimeparse(self.interval_start)
            pto = self._datetimeparse(self.interval_end)
            prange = "%02d:%02d - %02d:%02d" % (pfrom.hour,
                                                pfrom.minute, pto.hour, pto.minute)
            if now.date() == pfrom.date():
                return "Today, %s" % prange
            elif (pfrom.date() - now.date()).days == 1:
                return "Tomorrow, %s" % prange
            return "%d/%d, %s" % (pfrom.day, pfrom.month, prange)
        return None
