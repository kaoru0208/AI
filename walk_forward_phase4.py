#!/usr/bin/env python3
import datetime as dt

import matplotlib.pyplot as plt
import optuna
import pandas as pd
import yfinance as yf

from utils_cost import apply_cost  # ← 取引コスト関数

SYMBOL, START, END, WINDOW = "USDJPY=X", "2020-01-01", "2023-12-31", 126


def get_data():
    return yf.download(SYMBOL, start=START, end=END, progress=False, auto_adjust=True)


def equity_curve(close: pd.Series, fast: int, slow: int) -> pd.Series:
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    pos = (ema_fast > ema_slow).astype(int).replace(0, -1)
    ret = apply_cost(close.pct_change().fillna(0))  # コスト控除
    # ポジションは翌日リターンに適用（ルックアヘッド回避）
    strat = pos.shift(1).reindex(close.index).fillna(0) * ret
    return (1 + strat).cumprod()


def objective(trial, ins_close):
    f = trial.suggest_int("fast", 5, 20)
    s = trial.suggest_int("slow", f + 1, 60)
    eq = equity_curve(ins_close, f, s)
    return eq.iloc[-1] - 1, (1 - eq / eq.cummax()).max()


def walk_forward(df):
    results, equity_all = [], pd.Series(dtype=float)
    dates = pd.date_range(START, END, freq=f"{WINDOW}B")
    for st in dates:
        ins_end = st + dt.timedelta(days=WINDOW)
        oos_end = ins_end + dt.timedelta(days=WINDOW)
        if oos_end > df.index[-1]:
            break
        ins_close = df.loc[st:ins_end, "Close"]
        oos_close = df.loc[ins_end:oos_end, "Close"]

        study = optuna.create_study(directions=["maximize", "minimize"])
        study.optimize(
            lambda t: objective(t, ins_close), n_trials=30, show_progress_bar=False
        )
        best = study.best_trials[0].params
        eq_oos = equity_curve(oos_close, best["fast"], best["slow"])

        # 連結：最初だけそのまま、以降はレベル合わせ
        if equity_all.empty:
            equity_all = eq_oos / eq_oos.iloc[0]
        else:
            equity_all = pd.concat(
                [equity_all, equity_all.iloc[-1] * (eq_oos / eq_oos.iloc[0])]
            )

        results.append(
            {
                "start": st.date(),
                "end": oos_close.index[-1].date(),
                **best,
                "ret": eq_oos.iloc[-1] / eq_oos.iloc[0] - 1,
                "mdd": (1 - eq_oos / eq_oos.cummax()).max(),
            }
        )

    return pd.DataFrame(results), equity_all


if __name__ == "__main__":
    data = get_data()
    summary, equity = walk_forward(data)
    summary.to_csv("wf_summary.csv", index=False)
    equity.plot(title="Walk‑Forward Equity")
    plt.savefig("wf_equity.png")
    print("✅ wf_summary.csv と wf_equity.png を生成しました")
