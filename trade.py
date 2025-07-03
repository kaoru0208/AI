import time, logging, numpy as np
from oandapyV20 import API
from oandapyV20.endpoints.instruments import InstrumentsCandles
from oandapyV20.endpoints.orders import OrderCreate
import config
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.models import load_model
model = load_model("model.keras", compile=False)
model.compile(optimizer="adam", loss=MeanSquaredError())

logging.basicConfig(filename='trade.log',
                    level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')

api    = API(access_token=config.API_TOKEN)
buf    = []

while True:
    cndl = InstrumentsCandles(config.INSTRUMENT,
                              params={"count":1,"granularity":config.GRANULARITY})
    api.request(cndl)
    price = float(cndl.response["candles"][0]["mid"]["c"])
    buf.append(price)
    if len(buf)>config.WINDOW_SIZE: buf.pop(0)

    if len(buf)==config.WINDOW_SIZE:
        x = np.array(buf).reshape(1,config.WINDOW_SIZE,1)
        pred = model.predict(x/x.max(), verbose=0)[0][0]*max(buf)
        diff = pred - buf[-1]
        if abs(diff) < 0.0001:
            logging.info("HOLD")
        else:
            units = config.UNITS if diff>0 else -config.UNITS
            data  = {"order":{"units":str(units),"instrument":config.INSTRUMENT,
                              "timeInForce":"FOK","type":"MARKET","positionFill":"DEFAULT"}}
            try:
                oc = OrderCreate(config.ACCOUNT_ID, data=data); api.request(oc)
                price_exe = oc.response["orderFillTransaction"]["price"]
                logging.info(f"EXEC {units:+} @ {price_exe}")
            except Exception as e:
                logging.error(f"ORDER ERR {e}")
    time.sleep(60)
