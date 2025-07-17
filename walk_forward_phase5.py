#!/usr/bin/env python3
"""
walk_forward_phase5.py  ―  Walk‑Forward EMA Strategy
改良点:
  • 引数 --start / --cost をグローバル変数 START, COST に上書き
  • apply_cost で約定コストを控除
  • 不要な global 宣言を排除
"""
import argparse
import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
import yfinance as yf

# ── デフォルト値 ────────────────────────────────────────────────
START = "2015-01-01"  # CLI で上書き可
END = None  # 省略時 = 最新
WINDOW = 90  # in‑sample / out‑of‑sample 各ウィンドウ長（営業日）
COST = 0.0  # round‑trip cost, CLI で上書き可


# ── ヘルパ関数群 ────────────────────────────────────────────────
def get_data(symbol: str = "EURUSD=X", start=START, end=END) -> pd.DataFrame:
    df = yf.download(symbol, start, end, progress=False)[["Close"]]
    df.dropna(inplace=True)
    return df


def apply_cost(ret: pd.Series) -> pd.Series:
    """ラウンドトリップ・コストを控除したリターンを返す"""
    traded = ret.abs()
    return ret - traded * COST


def equity_curve(close: pd.Series, fast: int, slow: int) -> pd.Series:
    if fast >= slow:
        raise ValueError(f"fast({fast}) >= slow({slow}) になっています")
    if slow > 200:
        raise ValueError("slow は 200 以下を推奨します")

    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    pos = np.where(ema_fast > ema_slow, 1, -1)
    ret = apply_cost(close.pct_change().fillna(0))
    strat = pd.Series(pos, index=close.index).shift(1).fillna(0) * ret
    return (1 + strat).cumprod()


def objective(trial, ins_close):
    f = trial.suggest_int("fast", 5, 20)
    s = trial.suggest_int("slow", f + 1, 60)
    eq = equity_curve(ins_close, f, s)
    total_ret = eq.iat[-1] - 1
    mdd = (1 - eq / eq.cummax()).max()
    return total_ret, mdd  # maximize return, minimize MDD


def walk_forward(df: pd.DataFrame):
    results, equity_all = [], pd.Series(dtype=float)
    dates = pd.date_range(START, END or df.index[-1], freq=f"{WINDOW}B")
    for st in dates:
        ins_end = st + dt.timedelta(days=WINDOW)
        oos_end = ins_end + dt.timedelta(days=WINDOW)
        if oos_end > df.index[-1]:
            break

        ins_close = df.loc[st:ins_end, "Close"].squeeze()
        oos_close = df.loc[ins_end:oos_end, "Close"].squeeze()

        study = optuna.create_study(directions=["maximize", "minimize"])
        study.optimize(
            lambda t: objective(t, ins_close), n_trials=30, show_progress_bar=False
        )
        best = study.best_trials[0].params

        eq_oos = equity_curve(oos_close, best["fast"], best["slow"])
        equity_all = (
            (eq_oos / eq_oos.iat[0])
            if equity_all.empty
            else pd.concat([equity_all, equity_all.iat[-1] * (eq_oos / eq_oos.iat[0])])
        )

        results.append(
            {
                "start": st.date(),
                "end": oos_close.index[-1].date(),
                **best,
                "ret": eq_oos.iat[-1] / eq_oos.iat[0] - 1,
                "mdd": (1 - eq_oos / eq_oos.cummax()).max(),
            }
        )
    return pd.DataFrame(results), equity_all


# ── main ──────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Walk‑Forward EMA Strategy")
    ap.add_argument("--symbol", default="EURUSD=X")
    ap.add_argument("--start", default=START)
    ap.add_argument(
        "--cost", type=float, default=COST, help="round‑trip cost (e.g. 0.0002)"
    )
    args = ap.parse_args()

    # CLI 上書きを即反映
    START = args.start
    COST = args.cost

    data = get_data(args.symbol, START, END)
    summary, equity = walk_forward(data)

    summary.to_csv("wf_summary.csv", index=False)
    equity.plot(title=f"Walk‑Forward Equity  (cost={COST:.4%})")
    plt.savefig("wf_equity.png", dpi=150, bbox_inches="tight")
    print("✅ wf_summary.csv と wf_equity.png を生成しました")
