#!/usr/bin/env python3
"""
フェーズ3: マルチ目的 (累積リターン↑, 最大DD↓) Optuna
保存物 : equity.png, drawdown.png
"""
import matplotlib.pyplot as plt
import numpy as np
import optuna
import yfinance as yf

SYMBOL = "USDJPY=X"
START = "2020-01-01"
END = "2023-12-31"


def calc_equity(fast: int, slow: int):
    df = yf.download(SYMBOL, start=START, end=END, progress=False, auto_adjust=True)
    df["ema_fast"] = df["Close"].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df["Close"].ewm(span=slow, adjust=False).mean()
    df["pos"] = np.where(df["ema_fast"] > df["ema_slow"], 1, -1)
    df["ret"] = df["Close"].pct_change().fillna(0)
    strat_ret = df["pos"].shift() * df["ret"]
    equity = (1 + strat_ret).cumprod()
    return equity


# ---------- Optuna 目的関数 ----------
def objective(trial):
    fast = trial.suggest_int("fast", 5, 20)
    slow = trial.suggest_int("slow", fast + 1, 60)

    equity = calc_equity(fast, slow)
    cumret = equity.iloc[-1] - 1  # 目的1: 最大化
    mdd = (1 - equity / equity.cummax()).max()  # 目的2: 最小化
    return cumret, mdd


if __name__ == "__main__":
    study = optuna.create_study(
        directions=["maximize", "minimize"],
        sampler=optuna.samplers.TPESampler(multivariate=True),
    )
    study.optimize(objective, n_trials=50, show_progress_bar=True)

    best = study.best_trials[0]
    params = best.params
    print("🏆 Best params :", params)
    print(f"   Return={best.values[0]:.2%}, MaxDD={best.values[1]:.2%}")

    # もう一度ベストパラメータでエクイティを計算して保存
    eq = calc_equity(**params)
    dd = 1 - eq / eq.cummax()

    plt.figure()
    eq.plot(title="Equity Curve")
    plt.savefig("equity.png")
    plt.figure()
    dd.plot(title="Drawdown")
    plt.savefig("drawdown.png")
    print("📈 画像を保存しました → equity.png, drawdown.png")
