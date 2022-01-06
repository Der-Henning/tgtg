import logging
from prometheus_client import start_http_server, Gauge, Counter

log = logging.getLogger('tgtg')


class Metrics():
    def __init__(self, port=8000):
        self.port = port
        self.item_count = Gauge("tgtg_item_count", "Currently available bags", [
                                'item_id', 'display_name'])
        self.get_favorites_errors = Counter(
            "tgtg_get_favorites_errors", "Count of request errors fetching tgtg favorites")
        self.send_notifications = Counter(
            "tgtg_send_notifications", "Count of send notifications", ['item_id', 'display_name'])

    def enable_metrics(self):
        start_http_server(self.port)
        log.info("Metrics server startet on port %s", self.port)
