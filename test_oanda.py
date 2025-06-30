from dotenv import load_dotenv
import os, oandapyV20, oandapyV20.endpoints.accounts as acc

load_dotenv()
api = oandapyV20.API(
        access_token=os.getenv("OANDA_TOKEN"),
        environment=os.getenv("ENVIRONMENT", "practice"))
r = acc.AccountSummary(os.getenv("OANDA_ACCOUNT"))
print("残高:", api.request(r)["account"]["balance"])
