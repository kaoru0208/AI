def apply_cost(ret, cost=0.0002):
    """往復 0.02% のコストを各取引日に差し引く"""
    traded = ret.ne(0).astype(int)
    return ret - traded * cost
