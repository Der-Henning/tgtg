import requests

from tgtg_scanner.models.metrics import Metrics


def test_metrics():
    metrics = Metrics(8000)
    metrics.enable_metrics()
    res = requests.get("http://localhost:8000", timeout=10)

    assert res.ok
