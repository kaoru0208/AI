#!/bin/bash set -e

# --- 1) 必要ライブラリ ---
python -m pip install --upgrade numpy pandas scipy fredapi tradingeconomics \
                         prometheus-client discord-webhook tensorflow

# --- 2) config.py 追記（重複チェック付き） ---
grep -q "PROM_PUSH_URL" config.py || cat >> config.py << 'EOF'

# --- 追加パラメータ（自動追記） ---
PROM_PUSH_URL   = "http://localhost:9091"          # Prometheus Pushgateway
DISCORD_WEBHOOK = ""                               # Discord Webhook URL（任意）
TARGET_PAIRS    = ["USD_JPY", "EUR_USD", "GBP_JPY"]# 監視通貨ペア
MAX_VAR         = 0.02                             # 1‑day VaR 上限 (2 %)
EOF

# --- 3) 補助モジュール ---
cat > risk_engine.py << 'PY'
import numpy as np
def calc_portfolio_var(ret_mat, w, conf=0.99):
    cov = np.cov(ret_mat, rowvar=False)
    z   = 2.33 if conf==0.99 else 1.65
    return z * (w @ cov @ w.T) ** .5
def rebalance(w, target, current):
    if current == 0: return w
    scale = min(1, target / current)
    return w * scale
PY

cat > fundamentals.py << 'PY'
from fredapi import Fred
import tradingeconomics as te, os, pandas as pd
fred = Fred(api_key=os.getenv("FRED_KEY",""))
te.login()                                    # TRADINGECONOMICS_KEY env
def us10y():                                  # 米10年債利回り %
    try: return float(fred.get_series_latest_release("DGS10"))
    except: return None
def next_high_impact():
    df = te.getCalendarData(output_type='df', importance='High')
    return df[df['Date']>=pd.Timestamp.utcnow()].head(3)
PY

cat > lstm_model.py << 'PY'
import numpy as np, tensorflow as tf, os
def _file(pair): return f"lstm_{pair}.h5"
def train(series, pair, epochs=3):
    x = (series - series.mean()) / series.std()
    ds = tf.keras.preprocessing.timeseries_dataset_from_array(
            x[:-1,None], x[1:], sequence_length=20, batch_size=32)
    m = tf.keras.Sequential([tf.keras.layers.LSTM(32),
                             tf.keras.layers.Dense(1)])
    m.compile('adam','mse'); m.fit(ds, epochs=epochs, verbose=0)
    m.save(_file(pair))
def predict(series, pair):
    if not os.path.exists(_file(pair)): return 0
    m=tf.keras.models.load_model(_file(pair))
    x=series[-20:].values.reshape(1,20,1)
    return float(m(x, training=False)[0,0])
PY

cat > monitor.py << 'PY'
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import os, requests
REG = CollectorRegistry(); BAL = Gauge('fxbot_balance','',registry=REG)
def push(balance):
    BAL.set(balance)
    push_to_gateway(os.getenv('PROM_PUSH_URL',"http://localhost:9091"),
                    job='fxbot', registry=REG)
def alert(msg):
    url=os.getenv('DISCORD_WEBHOOK'); 
    if url: requests.post(url,json={'content':msg})
PY

# --- 4) メイン v3 ---
cat > trading_bot_v3.py << 'PY'
import time, numpy as np, pandas as pd, oandapyV20
import oandapyV20.endpoints.pricing as pr, oandapyV20.endpoints.orders as od
from oandapyV20.contrib.requests import MarketOrderRequest, TrailingStopLossDetails
import config, risk_engine as rk, fundamentals as fd, lstm_model as lm, monitor
api=oandapyV20.API(access_token=config.ACCESS_TOKEN, environment=config.API_ENV)
pairs=config.TARGET_PAIRS; hist={p:[] for p in pairs}; w=np.ones(len(pairs))/len(pairs)
def price_update():
    r=pr.PricingInfo(accountID=config.ACCOUNT_ID,
                     params={'instruments':','.join(pairs)})
    for p in api.request(r)['prices']:
        mid=(float(p['bids'][0]['price'])+float(p['asks'][0]['price']))/2
        hist[p['instrument']].append(mid)
def cycle():
    price_update();          # 価格更新
    if min(map(len,hist.values()))<50: return
    ret=np.column_stack([pd.Series(v).pct_change().dropna().values for v in hist.values()])
    var=rk.calc_portfolio_var(ret,w); w_adj=rk.rebalance(w,config.MAX_VAR,var)
    fcoef=0.5 if (rate:=fd.us10y()) and rate>4 else 1
    sig=np.array([np.sign(lm.predict(pd.Series(hist[p]),p) - hist[p][-1]) for p in pairs])
    bal=float(api.request(oandapyV20.endpoints.accounts.AccountDetails(config.ACCOUNT_ID))['account']['balance'])
    monitor.push(bal)
    for i,p in enumerate(pairs):
        units=int(1000*w_adj[i]*fcoef*sig[i]); 
        if units==0: continue
        req=MarketOrderRequest(instrument=p, units=units,
             trailingStopLossOnFill=TrailingStopLossDetails(distance=0.002).data)
        try:
            r=api.request(od.OrderCreate(config.ACCOUNT_ID,data=req.data))
            monitor.alert(f"✅ {p} {units:+} @ {r.get('orderFillTransaction',{}).get('price','')}")
        except Exception as e:
            monitor.alert(f"❌ {p} 発注失敗 {e}")
while True: cycle(); time.sleep(300)
PY

echo "=== ✔ アップグレード完了。起動 → python trading_bot_v3.py ==="

