from prometheus_client import start_http_server, Gauge, Counter

class Metrics():
    def __init__(self, port = 8000):
        self.port = port
        self.item_count = Gauge("tgtg_item_count", "Currently available bags", ['item_id', 'display_name'])
        self.get_favorites_errors = Counter("get_favorites_errors", "Count of request errors fetching tgtg favorites")
        self.send_notifications = Counter("send_notifications", "Count of send notifications")

    def enable_metrics(self):
        start_http_server(self.port)