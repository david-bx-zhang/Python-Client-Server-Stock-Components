def strategy_trend(price, mean, stdev):
    if price > mean + stdev:
        return 1
    elif price < mean - stdev:
        return -1
    else:
        return 0

def strategy_mean_reversion(price, meant, stdev):
    if price > meant + stdev:
        return -1
    elif price < mean - stdev:
        return 1
    else:
        return 0

