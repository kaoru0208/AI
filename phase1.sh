#!/usr/bin/env bash
set -euo pipefail
cd ~/projects/fxbot && source .venv/bin/activate
pip install --upgrade backtesting optuna
python - <<'PY'
import yaml,optuna,pathlib,pandas_ta as ta, pandas as pd
from optimize import objective
def add_indicators(df):
    df.ta.macd(append=True);df.ta.bbands(append=True);df.ta.adx(append=True)
    df['RSI']=ta.rsi(df.Close,length=11);return df
objective.__globals__['add_indicators']=add_indicators
study=optuna.create_study(direction='maximize');study.optimize(objective,n_trials=600)
pathlib.Path('best_params.yaml').write_text(yaml.dump(study.best_params))
PY
python -m backtest --pair EUR_USD --years 5 --save_csv results_phase1.csv
python -m trade_executor --live false --days 28
echo "🎉 Phase‑1 finished"
