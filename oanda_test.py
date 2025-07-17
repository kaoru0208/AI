from oandapyV20 import API
from oandapyV20.endpoints.accounts import AccountSummary

api = API(access_token="YOUR_REAL_V20_TOKEN")
print(api.request(AccountSummary(accountID="101‑001‑12345678‑001")))
