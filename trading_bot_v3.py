import time

import numpy as np
import oandapyV20
import oandapyV20.endpoints.orders as od
import oandapyV20.endpoints.pricing as pr
import pandas as pd
from oandapyV20.contrib.requests import MarketOrderRequest, TrailingStopLossDetails

import config
import fundamentals as fd
import lstm_model as lm
import monitor
import risk_engine as rk

api = oandapyV20.API(access_token=config.ACCESS_TOKEN, environment=config.API_ENV)
pairs = config.TARGET_PAIRS
hist = {p: [] for p in pairs}
w = np.ones(len(pairs)) / len(pairs)


def price_update():
    r = pr.PricingInfo(
        accountID=config.ACCOUNT_ID, params={"instruments": ",".join(pairs)}
    )
    for p in api.request(r)["prices"]:
        mid = (float(p["bids"][0]["price"]) + float(p["asks"][0]["price"])) / 2
        hist[p["instrument"]].append(mid)


def cycle():
    price_update()  # 価格更新
    if min(map(len, hist.values())) < 50:
        return
    ret = np.column_stack(
        [pd.Series(v).pct_change().dropna().values for v in hist.values()]
    )
    var = rk.calc_portfolio_var(ret, w)
    w_adj = rk.rebalance(w, config.MAX_VAR, var)
    fcoef = 0.5 if (rate := fd.us10y()) and rate > 4 else 1
    sig = np.array(
        [np.sign(lm.predict(pd.Series(hist[p]), p) - hist[p][-1]) for p in pairs]
    )
    bal = float(
        api.request(oandapyV20.endpoints.accounts.AccountDetails(config.ACCOUNT_ID))[
            "account"
        ]["balance"]
    )
    monitor.push(bal)
    for i, p in enumerate(pairs):
        units = int(1000 * w_adj[i] * fcoef * sig[i])
        if units == 0:
            continue
        req = MarketOrderRequest(
            instrument=p,
            units=units,
            trailingStopLossOnFill=TrailingStopLossDetails(distance=0.002).data,
        )
        try:
            r = api.request(od.OrderCreate(config.ACCOUNT_ID, data=req.data))
            monitor.alert(
                f"✅ {p} {units:+} @ {r.get('orderFillTransaction',{}).get('price','')}"
            )
        except Exception as e:
            monitor.alert(f"❌ {p} 発注失敗 {e}")


while True:
    cycle()
    time.sleep(300)
