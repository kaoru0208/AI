from os import getenv

from dotenv import load_dotenv

load_dotenv()
OANDA_TOKEN = getenv("OANDA_TOKEN")
OANDA_ACCOUNT = getenv("OANDA_ACCOUNT")
GRANULARITY = "M1"
BASE_CCY = "JPY"
