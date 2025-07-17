import vectorbt as vbt
import yfinance as yf

import strategy


def run_backtest(adx_th: int = 25):
    # --- ① データ取得 ------------------------------------------------
    ohlc = yf.download(
        "EURUSD=X",
        start="2020-01-01",  # ← 足りなければ開始日をもっと過去に
        auto_adjust=False,
        progress=False,
        interval="1d",
    )

    # --- ② 取得データの概要を確認（デバッグ） -------------------------
    print("OHLC shape =", ohlc.shape)
    print(ohlc.head(3), "\n")  # 先頭 3 行だけ表示

    # --- ③ シグナル生成 & ポートフォリオ -----------------------------
    sig = strategy.build_signals(ohlc, adx_th)
    price = (
        ohlc["Close_EURUSD=X"] if "Close_EURUSD=X" in ohlc.columns else ohlc["Close"]
    )

    return vbt.Portfolio.from_signals(
        price,
        sig["entry"],
        sig["exit"],
        freq="1D",
        fees=0.0002,
    )


if __name__ == "__main__":
    print(run_backtest().stats())
    # ---- ここから追加 ----
    import datetime
    import sys

    print("DONE", datetime.datetime.now(), file=sys.stderr)
    # ---- ここまで ----
