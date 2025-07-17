import os

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

REG = CollectorRegistry()
API_CALL_G = Gauge("fxbot_api_calls_total", "Total API calls", registry=REG)
NEWS429_G = Gauge("fxbot_news429_total", "NewsAPI 429 errors", registry=REG)


def push(api_calls=0, news429=0):
    API_CALL_G.set(api_calls)
    NEWS429_G.set(news429)
    push_to_gateway(
        os.getenv("PROM_PUSH_URL", "http://localhost:9091"),
        job="fxbot_ext",
        registry=REG,
    )
