from prometheus_client import Gauge, start_http_server

balance_g = Gauge("fxbot_balance_jpy", "Account balance (JPY)")
dd_g = Gauge("fxbot_drawdown", "Drawdown ratio")
start_http_server(9100)


def update(balance: float, drawdown: float):
    balance_g.set(balance)
    dd_g.set(drawdown)
