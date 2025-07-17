import math

import optuna
import yfinance as yf
from backtesting import Backtest, Strategy

from strategy import add_indicators, generate_signals


def load_price_data(symbol: str = "EURUSD=X", years: int = 5):
    """Load historical price data (default: last 5 years of given symbol)."""
    import datetime

    end = datetime.date.today()
    start = end - datetime.timedelta(days=years * 365)
    # If symbol like "EUR_USD" is given, convert to Yahoo Finance ticker
    if "_" in symbol and not symbol.endswith("=X"):
        symbol = symbol.replace("_", "") + "=X"
    df = yf.download(symbol, start=start, end=end)
    # Ensure column names are in expected format
    df.rename(
        columns=str.capitalize, inplace=True
    )  # 'Open','High','Low','Close','Volume'
    return df


def objective(trial: optuna.trial.Trial):
    # Suggest values for each tunable parameter
    params = {
        "fast": trial.suggest_int("fast", 8, 16, step=2),
        "slow": trial.suggest_int("slow", 20, 30, step=2),
        "signal": trial.suggest_int("signal", 6, 12),
        "bb_length": trial.suggest_int("bb_length", 18, 24),
        "bb_std": trial.suggest_float("bb_std", 1.5, 2.5, step=0.1),
        "adx_th": trial.suggest_int("adx_th", 20, 40),
    }
    # Load data and add indicators
    df = load_price_data(symbol=optuna_symbol, years=optuna_years)
    df = add_indicators(
        df,
        fast=params["fast"],
        slow=params["slow"],
        signal=params["signal"],
        bb_length=params["bb_length"],
        bb_std=params["bb_std"],
    )
    df = generate_signals(df, params)

    # Define trading strategy using the precomputed signals
    class SignalStrategy(Strategy):
        def init(self):
            pass  # Indicators already computed in df

        def next(self):
            # Use the last value of 'long'/'short' signals for current step
            if self.data.long[-1] and not self.position:
                self.buy()
            elif self.data.short[-1] and not self.position:
                self.sell()
            # Close and reverse logic
            elif self.position.is_long and self.data.short[-1]:
                self.position.close()
                self.sell()
            elif self.position.is_short and self.data.long[-1]:
                self.position.close()
                self.buy()

    # Run backtest on this trial's parameters
    bt = Backtest(df, SignalStrategy, cash=10000, commission=0.0)
    stats = bt.run()
    pf = stats["Profit Factor"]
    # Handle inf/nan PF (e.g., no trades scenario)
    if pf is None or math.isnan(pf) or math.isinf(pf):
        pf = 0.0
    return pf


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pair", type=str, default="EURUSD=X", help="Ticker or symbol for data"
    )
    parser.add_argument(
        "--years", type=int, default=5, help="Number of years of historical data to use"
    )
    parser.add_argument(
        "--trials", type=int, default=100, help="Number of optimization trials"
    )
    parser.add_argument(
        "--direction",
        type=str,
        default="maximize",
        help="Optimization direction: maximize or minimize",
    )
    args = parser.parse_args()
    # Set global for use in objective (optuna doesn't pass args easily into objective)
    global optuna_symbol, optuna_years
    optuna_symbol = args.pair
    optuna_years = args.years
    # Set up and run Optuna study
    study = optuna.create_study(direction=args.direction)
    study.optimize(objective, n_trials=args.trials)
    # Output best result
    print("Best parameters:", study.best_params)
    print("Best Profit Factor:", study.best_value)
    # Save best params to file
    with open("best_params.json", "w") as f:
        json.dump(study.best_params, f, indent=4)
    print("Saved best parameters to best_params.json")
