#!/usr/bin/env bash
set -e
python -m pip install --quiet --upgrade fredapi pandas requests
cat > fundamentals.py <<'PY'
import os, datetime as dt
from fredapi import Fred
fred = Fred(api_key=os.getenv("FRED_KEY", ""))
_SERIES = {"nfp":"PAYEMS","cpi":"CPIAUCSL","unrate":"UNRATE",
           "us10y":"DGS10","fedfunds":"DFEDTARU"}
def _latest_single(s):       # 1件だけ取得
    try: return float(fred.get_series_latest_release(s).dropna().iloc[-1])
    except Exception: return None
def latest_values():         # 辞書で返す
    return {k:_latest_single(s) for k,s in _SERIES.items()}
def macro_factor():
    v=latest_values(); nfp,vu=v["nfp"],v["unrate"]
    if None in (nfp,vu): return 1.0
    try:
        prev=float(fred.get_series("PAYEMS",
                 dt.date.today()-dt.timedelta(days=90),
                 dt.date.today()-dt.timedelta(days=60)).dropna().iloc[-1])
    except Exception: return 1.0
    if nfp-prev>0 and vu<4.5: return 1.2
    if nfp-prev<0 and vu>5:   return 0.8
    return 1.0
PY
echo "✔ fundamentals.py generated"
[ -f ~/Library/LaunchAgents/com.fxbot.bot.plist ] && \
  launchctl unload -w ~/Library/LaunchAgents/com.fxbot.bot.plist 2>/dev/null && \
  launchctl load  -w ~/Library/LaunchAgents/com.fxbot.bot.plist && \
  echo "✔ bot reloaded"
