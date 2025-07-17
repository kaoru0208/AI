#!/usr/bin/env python3
"""
フェーズ2: EMAクロスオーバー戦略の検証 & 可視化
  - 通貨ペア : USD/JPY ('USDJPY=X')
  - 期間     : 2020-01-01 〜 2023-12-31（学習期間＋α）
  - 指標     : 最終累積リターン, 最大ドローダウン, シャープレシオ
"""
import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf

# === ▼ フェーズ1で得たベストパラメータを手入力 or JSONから読み込み ▼ ===
BEST = dict(fast=5, slow=15, signal=14)  # ← 必要に応じて書き換え

# === 1) データ取得 ============================================================
symbol = "USDJPY=X"
start = "2020-01-01"
end = "2023-12-31"
df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=True)

# === 2) シグナル生成 & リターン計算 ==========================================
df["ema_fast"] = df["Close"].ewm(span=BEST["fast"], adjust=False).mean()
df["ema_slow"] = df["Close"].ewm(span=BEST["slow"], adjust=False).mean()
df["position"] = np.where(df["ema_fast"] > df["ema_slow"], 1, -1)
df["ret"] = df["Close"].pct_change().fillna(0)
df["strat_ret"] = df["position"].shift() * df["ret"]
df["equity"] = (1 + df["strat_ret"]).cumprod()  # 純資産曲線

# === 3) 性能指標 =============================================================
cum_return = df["equity"].iloc[-1] - 1
# 最大ドローダウン
rolling_max = df["equity"].cummax()
drawdown = 1 - df["equity"] / rolling_max
max_dd = drawdown.max()
# シャープレシオ（√252 で年率換算、リスクフリー 0% 仮定）
sharpe = (df["strat_ret"].mean() / df["strat_ret"].std()) * np.sqrt(252)

# 結果表示
print(f"累積リターン : {cum_return:.2%}")
print(f"最大DD       : {max_dd:.2%}")
print(f"シャープ比    : {sharpe:.3f}")

# === 4) グラフ描画 ============================================================
plt.figure()
df["equity"].plot(title="Equity Curve (USDJPY EMA Cross)")

plt.figure()
drawdown.plot(title="Drawdown")

plt.show()
