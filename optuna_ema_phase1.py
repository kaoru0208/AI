#!/usr/bin/env python3
"""
フェーズ1: Optuna を用いた EMA クロスオーバー最適化
通貨ペア: USD/JPY（Yahoo! Finance シンボル 'USDJPY=X'）
期間   : 2022‑01‑01 ～ 2023‑12‑31
評価指標: 最終累積リターン
"""

import numpy as np
import optuna
import yfinance as yf


# ---- 目的関数 ----
def objective(trial):
    fast = trial.suggest_int("fast", 5, 20)
    slow = trial.suggest_int("slow", fast + 1, 60)  # fast より遅い
    trial.suggest_int("signal", 5, 20)  # 今回は未使用（将来拡張用）

    df = yf.download("USDJPY=X", start="2022-01-01", end="2023-12-31", progress=False)
    if df.empty:
        return 0.0

    df["ema_fast"] = df["Close"].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df["Close"].ewm(span=slow, adjust=False).mean()

    df["position"] = np.where(df["ema_fast"] > df["ema_slow"], 1, -1)
    df["daily_ret"] = df["Close"].pct_change().fillna(0)
    strat_ret = (df["position"].shift() * df["daily_ret"]).cumsum()

    return strat_ret.iloc[-1]  # 最終累積リターンを最大化


# ---- Optuna で最適化 ----
if __name__ == "__main__":
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=30)

    print("Best params :", study.best_params)
    print("Best score  :", study.best_value)
