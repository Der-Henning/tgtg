import datetime


class Item():
    ATTRS = ["item_id", "items_available", "display_name",
             "price", "currency", "pickupdate"]

    def __init__(self, data):
        self.item_id = data["item"]["item_id"]
        self.items_available = data["items_available"]
        self.display_name = data["display_name"]
        self.price = data["item"]["price_including_taxes"]["minor_units"] / 100
        self.currency = data["item"]["price_including_taxes"]["code"]
        if 'pickup_interval' in data:
            self.interval_start = data['pickup_interval']['start']
            self.interval_end = data['pickup_interval']['end']

    @staticmethod
    def _issameday(interval_start: datetime, interval_end: datetime):
        return (
            interval_start.day == interval_end.day and
            interval_start.month == interval_end.month and
            interval_start.year == interval_end.year
        )

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
            if self._issameday(pfrom, now):
                return "Today, %s" % prange
            return "%d/%d, %s" % (pfrom.day, pfrom.month, prange)
        return None
