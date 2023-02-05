import requests

from models.metrics import Metrics


def test_metrics():
    metrics = Metrics(8000)
    metrics.enable_metrics()
    res = requests.get("http://localhost:8000")

    assert res.ok
