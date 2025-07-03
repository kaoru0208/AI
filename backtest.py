import logging, numpy as np, pandas as pd
from oandapyV20 import API
from oandapyV20.endpoints.instruments import InstrumentsCandles
import config
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.models import load_model
model = load_model("model.keras", compile=False)
model.compile(optimizer="adam", loss=MeanSquaredError())

logging.basicConfig(filename='backtest.log',
                    level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')

api = API(access_token=config.API_TOKEN)
candles = InstrumentsCandles(config.INSTRUMENT,
                             params={"count":500,"granularity":config.GRANULARITY})
api.request(candles)
prices = [float(c["mid"]["c"]) for c in candles.response["candles"] if c["complete"]]
df = pd.DataFrame(prices, columns=["close"])

win, trades, budget, peak = 0, 0, 1_000_000, 1_000_000
for i in range(config.WINDOW_SIZE, len(df)-1):
    seq = df.close.iloc[i-config.WINDOW_SIZE:i].values.reshape(1,config.WINDOW_SIZE,1)
    seq = seq/seq.max()
    pred = model.predict(seq, verbose=0)[0][0]*df.close.iloc[i-config.WINDOW_SIZE:i].max()
    cur, nxt = df.close.iloc[i], df.close.iloc[i+1]
    diff = nxt-cur
    if (pred>cur and diff>0) or (pred<cur and diff<0):
        win += 1
    trades += 1
    budget += diff*config.UNITS
    peak = max(peak, budget)
dd = peak - budget
print(f"Trades={trades}, Win%={win/trades*100:.2f}, P/L={budget-1_000_000:.0f}, MaxDD={dd:.0f}")
