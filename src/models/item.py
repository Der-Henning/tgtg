import datetime

class Item():
    ATTRS = ["item_id", "items_available", "display_name", "price", "currency"]

    def __init__(self, data):
        self.item_id = data["item"]["item_id"]
        self.items_available = data["items_available"]
        self.display_name = data["display_name"]
        self.price = data["item"]["price_including_taxes"]["minor_units"] / 100
        self.currency = data["item"]["price_including_taxes"]["code"]
        if 'pickup_interval' in data:
            self.interval_start = data['pickup_interval']['start']
            self.interval_end = data['pickup_interval']['end']

    def issameday(self, d1, d2):
        return (d1.day == d2.day and d1.month == d2.month and d1.year == d2.year)
    
    def datetimeparse(self, datestr):
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        value = datetime.datetime.strptime(datestr, fmt)
        return value.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)


    def pickupdate(self):
        now = datetime.datetime.now()
        pfrom = self.datetimeparse(self.interval_start)
        pto = self.datetimeparse(self.interval_end)
        prange = "%02d:%02d - %02d:%02d" % (pfrom.hour, pfrom.minute, pto.hour, pto.minute)
        if self.issameday(pfrom, now):
            return "Today, %s" % prange

        return "%d/%d, %s" % (pfrom.day, pfrom.month, prange)
