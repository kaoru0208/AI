import numpy as np


def calc_portfolio_var(ret_mat, w, conf=0.99):
    cov = np.cov(ret_mat, rowvar=False)
    z = 2.33 if conf == 0.99 else 1.65
    return z * (w @ cov @ w.T) ** 0.5


def rebalance(w, target, current):
    if current == 0:
        return w
    scale = min(1, target / current)
    return w * scale
