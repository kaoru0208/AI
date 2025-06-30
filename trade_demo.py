#!/usr/bin/env python3
import os, sys, time, csv, json, datetime, pathlib
import numpy as np, tensorflow as tf, oandapyV20
import oandapyV20.endpoints.instruments as ins
import oandapyV20.endpoints.positions   as pos
import oandapyV20.endpoints.pricing     as prc
from oandapyV20.endpoints.orders    import OrderCreate
from oandapyV20.endpoints.positions import PositionClose

# --- 必須設定 ------------------------------------------------------
ACCOUNT_ID   = os.getenv("ACC")         # 事前に export 済み
ACCESS_TOKEN = os.getenv("TOK")
PAIR         = "USD_JPY"
LOT          = 1000
MAX_UNITS    = 20000
TP_PCT = SL_PCT = 0.30                  # ±0.3 %
K_VOL   = 0.02
LOGFILE = pathlib.Path.home() / "fxbot_log.csv"
WEBHOOK = "https://discord.com/api/webhooks/XXXXXXXX"   # ←自分の URL

# --- OANDA API とモデル -------------------------------------------
api   = oandapyV20.API(access_token=ACCESS_TOKEN, environment="practice")
model = tf.keras.models.load_model(str(pathlib.Path.home() /
                                       "projects/fxbot/lstm_fx.h5"),
                                   compile=False)

# --- 共通関数 ------------------------------------------------------
def market_open(retry=3) -> bool:
    for _ in range(retry):
        try:
            r = prc.PricingInfo(accountID=ACCOUNT_ID,
                                params={"instruments": PAIR})
            api.request(r)
            return r.response["prices"][0]["tradeable"]
        except Exception as e:
            if "not tradable" in str(e) or "Market is closed" in str(e):
                return False
            time.sleep(2)
    return False

def latest(n=60):
    r = ins.InstrumentsCandles(instrument=PAIR,
                               params={"count": n, "granularity": "M1",
                                       "price": "M"})
    api.request(r)
    close = np.array([float(c['mid']['c']) for c in r.response['candles']])
    z = (close - close.mean()) / (close.std() + 1e-6)
    return z.reshape(1, -1, 1)

def last_price():
    r = prc.PricingInfo(accountID=ACCOUNT_ID,
                        params={"instruments": PAIR})
    api.request(r)
    return float(r.response["prices"][0]["bids"][0]["price"])

def units_now():
    r = pos.OpenPositions(accountID=ACCOUNT_ID); api.request(r)
    p = [p for p in r.response['positions'] if p['instrument'] == PAIR]
    return int(float(p[0]['long']['units']) + float(p[0]['short']['units'])) if p else 0

def close_all(side):            # "longUnits" / "shortUnits"
    api.request(PositionClose(accountID=ACCOUNT_ID,
                              instrument=PAIR, data={side: "ALL"}))
    print("✔ CLOSE", side)

def discord(msg):
    os.system(f'curl -s -H "Content-Type: application/json" -X POST '
              f'-d \'{{"content":"{msg}"}}\' "{WEBHOOK}"')

def send_order(side, prob):
    p  = last_price()
    tp = p*(1-TP_PCT/100) if side == "SELL" else p*(1+TP_PCT/100)
    sl = p*(1+SL_PCT/100) if side == "SELL" else p*(1-TP_PCT/100)
    data = {"order": {"units": str(LOT if side=="BUY" else -LOT),
                      "instrument": PAIR,
                      "type": "MARKET", "positionFill": "DEFAULT",
                      "takeProfitOnFill": {"price": f"{tp:.3f}"},
                      "stopLossOnFill":   {"price": f"{sl:.3f}"}}}
    r = api.request(OrderCreate(accountID=ACCOUNT_ID, data=data))
    oid = r["orderFillTransaction"]["id"]
    print("✔ ORDER", oid, side, "@", p)
    discord(f"ORDER {side} id={oid} prob={prob:.3f}")

# --- duplicate guard ----------------------------------------------
FLAG = pathlib.Path.home()/".fxbot_state.json"
def need_trade(sig):
    if not FLAG.exists():
        FLAG.write_text(json.dumps({"last": sig}))
        return sig != "WAIT"
    st = json.loads(FLAG.read_text())
    if sig == st["last"]: return False
    st["last"] = sig; FLAG.write_text(json.dumps(st))
    return sig != "WAIT"
# ------------------------------------------------------------------

if __name__ == "__main__":
    if not market_open():
        print("Market closed – sleeping 5 min")
        time.sleep(300); sys.exit(0)

    x      = latest()
    prob   = float(model.predict(x)[0][0])
    vol    = float(np.std(x))
    thB, thS = 0.5 + K_VOL/vol, 0.5 - K_VOL/vol
    sig    = "BUY" if prob > thB else "SELL" if prob < thS else "WAIT"
    now    = datetime.datetime.now().astimezone().strftime("%F %T")
    print(f"{now}  prob={prob:.3f}  vol={vol:.3f}  ⇒  {sig}")

    if need_trade(sig) and sig != "WAIT":
        pos = units_now()
        if sig == "BUY"  and pos < 0: close_all("shortUnits")
        if sig == "SELL" and pos > 0: close_all("longUnits")
        if abs(units_now()) < MAX_UNITS:
            send_order(sig, prob)
        else:
            print("SKIP max‑position")
    else:
        print("SKIP duplicate / wait")

    with LOGFILE.open("a", newline="") as f:
        csv.writer(f).writerow([now, prob, vol, sig, units_now()])

