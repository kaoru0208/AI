import oandapyV20
import pytest


@pytest.fixture(autouse=True)
def dummy_oanda_env(monkeypatch):
    monkeypatch.setenv("OANDA_TOKEN", "DUMMY")
    monkeypatch.setenv("OANDA_ACCOUNT", "000-000-00000000-000")

    class _Dummy(dict):
        def __init__(self):
            super().__init__(account={"balance": "10000"})

    monkeypatch.setattr(oandapyV20.oandapyV20.API, "request", lambda *a, **kw: _Dummy())
