import pandas as pd, numpy as np, logging
from oandapyV20 import API
from oandapyV20.endpoints.instruments import InstrumentsCandles
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
import config                        # ← config.py を読む

logging.basicConfig(filename='train.log',
                    level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')

api = API(access_token=config.API_TOKEN)
params = {"count": 1000, "granularity": config.GRANULARITY}
candles = InstrumentsCandles(config.INSTRUMENT, params=params)
api.request(candles)
prices = [float(c["mid"]["c"]) for c in candles.response["candles"] if c["complete"]]

df = pd.DataFrame(prices, columns=["close"])
window = config.WINDOW_SIZE
X, y = [], []
for i in range(len(df)-window):
    X.append(df.close.iloc[i:i+window].values)
    y.append(df.close.iloc[i+window])
X = np.array(X).reshape(-1, window, 1)
y = np.array(y)
train = int(len(X)*0.8)
Xtr, Xte, ytr, yte = X[:train], X[train:], y[:train], y[train:]
scale = Xtr.max()
Xtr, Xte, ytr, yte = Xtr/scale, Xte/scale, ytr/scale, yte/scale

model = Sequential([LSTM(50, input_shape=(window,1)), Dense(1)])
model.compile(optimizer='adam', loss='mse')
cb = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
model.fit(Xtr, ytr, epochs=50, batch_size=32, validation_data=(Xte,yte), callbacks=[cb])
model.save("model.keras")
print("✅  model.keras saved")
