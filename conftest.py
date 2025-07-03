import os, pytest
@pytest.fixture(autouse=True, scope="session")
def _patch_oanda_env(monkeypatch):
    monkeypatch.setenv("OANDA_TOKEN", "DUMMY")
    monkeypatch.setenv("OANDA_ACCOUNT", "000-000-00000000-000")
