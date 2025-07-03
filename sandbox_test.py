from dotenv import load_dotenv
load_dotenv()                       # .env を読む

import os, oandapyV20
import oandapyV20.endpoints.accounts as acc

TOKEN   = os.getenv("OANDA_API_TOKEN")
ACCOUNT = os.getenv("OANDA_ACCOUNT_ID")

api = oandapyV20.API(access_token=TOKEN, environment="practice")  # デモ口座は practice
r   = acc.AccountDetails(accountID=ACCOUNT)
print("=== 口座残高 ===")
print(api.request(r)["account"]["balance"])
