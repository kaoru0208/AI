import os

import requests
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

REG = CollectorRegistry()
BAL = Gauge("fxbot_balance", "", registry=REG)


def push(balance):
    BAL.set(balance)
    push_to_gateway(
        os.getenv("PROM_PUSH_URL", "http://localhost:9091"), job="fxbot", registry=REG
    )


def alert(msg):
    url = os.getenv("DISCORD_WEBHOOK")
    if url:
        requests.post(url, json={"content": msg})
