set -e
python -m pip install --upgrade fredapi pandas requests

cat > fundamentals.py <<'PY'
import os, datetime as dt
from fredapi import Fred
fred = Fred(api_key=os.getenv("FRED_KEY"))
_SERIES = {"nfp":"PAYEMS","cpi":"CPIAUCSL","unrate":"UNRATE","us10y":"DGS10","fedfunds":"DFEDTARU"}
def latest_values():
    today=dt.date.today(); vals={}
    for k,s in _SERIES.items():
        try:
            vals[k]=float(fred.get_series(s,today-dt.timedelta(days=30),today).dropna().iloc[-1])
        except: vals[k]=None
    return vals
def macro_factor():
    vals=latest_values(); nfp,unemp=vals["nfp"],vals["unrate"]
    if None in (nfp,unemp): return 1.0
    prev=fred.get_series(_SERIES["nfp"],dt.date.today()-dt.timedelta(days=60),
                         dt.date.today()-dt.timedelta(days=30)).dropna().iloc[-1]
    return 1.2 if nfp-prev>0 and unemp<4.5 else 0.8 if nfp-prev<0 and unemp>5 else 1.0
PY

echo "✔ fundamentals.py を FRED 版に置換済み"

# macOS launchd で動かしている場合のみ自動再起動
if [ -f ~/Library/LaunchAgents/com.fxbot.bot.plist ]; then
  launchctl unload -w ~/Library/LaunchAgents/com.fxbot.bot.plist 2>/dev/null || true
  launchctl load  -w ~/Library/LaunchAgents/com.fxbot.bot.plist
  echo "✔ launchd ボットを再起動しました"
fi
echo "=== FRED パッチ適用 完了 ==="
