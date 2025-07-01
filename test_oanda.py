import os

import oandapyV20
import oandapyV20.endpoints.accounts as acc
from dotenv import load_dotenv

load_dotenv(".env")  # .env を読む

API = oandapyV20.API(
    access_token=os.getenv("OANDA_API_TOKEN"),
    environment="practice",
)
ACCOUNT = os.getenv("OANDA_ACCOUNT_ID")  # ← これを先に定義（F821 対策）


def test_balance_is_positive():
    """残高が 0 より大きいことを確認する簡易テスト"""
    r = acc.AccountDetails(accountID=ACCOUNT)
    balance = float(API.request(r)["account"]["balance"])
    assert balance > 0
