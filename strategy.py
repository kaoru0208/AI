import pandas as pd
import pandas_ta as ta


# ---------- ヘルパー ----------
def flatten_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance MultiIndex → 単一列に変換"""
    if isinstance(df.columns, pd.MultiIndex):
        if len(df.columns.levels[1]) == 1:  # 単一ティッカー
            df.columns = df.columns.get_level_values(0)
        else:  # 複数ティッカー
            df.columns = ["_".join(col).strip() for col in df.columns.to_flat_index()]
    return df


# ---------- 指標追加 ----------
def add_indicators(
    df, *, fast, slow, signal, bb_length, bb_std, adx_len=14, **_ignored
):
    """
    fast/slow/signal/bb_length/bb_std だけ利用し、その他の
    キーワード (adx_th など) は無視しても安全なように **_ignored を許容。
    """
    df = flatten_ohlc(df)

    macd = ta.macd(df["Close"], fast=fast, slow=slow, signal=signal)
    bb = ta.bbands(df["Close"], length=bb_length, std=bb_std)
    adx = ta.adx(df["High"], df["Low"], df["Close"], length=adx_len)

    return pd.concat([df, macd, bb, adx], axis=1)


# ---------- シグナル生成 ----------
def generate_signals(df, p):
    macd_hist = f"MACDh_{p['fast']}_{p['slow']}_{p['signal']}"
    bb_lower = f"BBL_{p['bb_length']}_{p['bb_std']}"
    bb_upper = f"BBU_{p['bb_length']}_{p['bb_std']}"
    adx_col = "ADX_14"  # adx_len は固定 14 で計算

    df["long"] = (
        (df[macd_hist] > 0)
        & (df[macd_hist].shift(1) <= 0)
        & (df[adx_col] > p["adx_th"])
        & (df[bb_lower] > df["Close"])
    )
    df["short"] = (
        (df[macd_hist] < 0)
        & (df[macd_hist].shift(1) >= 0)
        & (df[adx_col] > p["adx_th"])
        & (df[bb_upper] < df["Close"])
    )
    return df
