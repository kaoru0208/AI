import datetime as dt

import pandas as pd

now = dt.datetime.utcnow().isoformat(timespec="seconds")
pd.DataFrame([{"time": now, "close": 1.2345}]).to_csv(
    "data.csv", mode="a", index=False, header=False
)
