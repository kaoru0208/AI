import datetime as dt, csv, oandapyV20, oandapyV20.endpoints.instruments, os
from dotenv import load_dotenv; load_dotenv()

PAIR = "USD_JPY"
GRAN = "M1"
COUNT_PER_REQ = 5000          # OANDA の上限

api = oandapyV20.API(environment=os.getenv("ENVIRONMENT"),
                     access_token=os.getenv("OANDA_TOKEN"))

end_time = dt.datetime.utcnow()          # 最新から遡って取る
rows = []

while len(rows) < 25000:                # ← 取りたい本数を変更可
    params = {
        "granularity": GRAN,
        "price": "M",
        "count": COUNT_PER_REQ,
        "to": end_time.isoformat("T") + "Z"
    }
    r = api.request(
        oandapyV20.endpoints.instruments.InstrumentsCandles(PAIR, params=params)
    )
    candles = r["candles"]
    if not candles:
        break
    rows[0:0] = candles                 # 先頭に挿入して時系列を昇順に保つ
    end_time = dt.datetime.fromisoformat(candles[0]["time"][:-1])

print(f"downloaded {len(rows)} candles")

with open("candles_USD_JPY_M1.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["time", "open", "high", "low", "close", "volume"])
    for c in rows:
        w.writerow([
            c["time"],
            c["mid"]["o"],
            c["mid"]["h"],
            c["mid"]["l"],
            c["mid"]["c"],
            c["volume"],
        ])
print("CSV saved:", f.name, os.path.getsize(f.name)/1024/1024, "MB")
