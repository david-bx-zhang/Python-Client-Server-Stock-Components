import json
import numpy as np
import pandas as pd
import re
from datetime import datetime, timedelta

# helper fn
def strategy(price, mean, stdev):
    if price > mean + stdev:
        return 1
    elif price < mean - stdev:
        return -1
    else:
        return 0
        
class Ticker(object):

    def __init__(self, ticker, interval=None, prices=None):
        self.ticker = ticker
        self.interval = interval
        self.prices = prices

        df = pd.DataFrame.from_dict(prices, orient='index', columns=['price'])

        df.index = pd.to_datetime(df.index)
        rollstdev = df.rolling('1d', min_periods=1).std()
        rollmean = df.rolling('1d', min_periods=1).mean()
        df['rollmean'] = rollmean
        df['rollstdev'] = rollstdev
        df['signal'] = df.apply(lambda x: strategy(x['price'], x['rollmean'], x['rollstdev']), axis=1)
        df['position'] = 0
        df['pnl'] = 0

        for i in range(1, len(df)):
            df.loc[df.index[i], 'position'] = df.loc[df.index[i-1], 'position'] + df.loc[df.index[i], 'signal']
            df.loc[df.index[i], 'pnl'] = df.loc[df.index[i-1], 'pnl'] + df.loc[df.index[i-1], 'position'] * (df.loc[df.index[i], 'price'] - df.loc[df.index[i-1], 'price'])

        self.df = df
        self.latest_ts = str(self.df.index[-1])
        self.latest_price = float(self.df.loc[self.latest_ts]['price'])
        self.latest_signal = float(self.df.loc[self.latest_ts]['signal'])
    
    def add_price(self, timestamp, price):

        row = {}
        
        if isinstance(timestamp, int):
            timestamp = pd.to_datetime(timestamp, unit='s')
        else:
            timestamp = pd.to_datetime(timestamp)
        
        cur_range = self.df.loc[str(timestamp - pd.offsets.Day(1)):]
        cur_range_list = cur_range['price'].tolist()
        cur_range_list.append(price)
        cur_range_list = [float(i) for i in cur_range_list]
        cur_mean = np.mean(cur_range_list)
        cur_stdev = np.std(cur_range_list)

        cur_signal = strategy(price, cur_mean, cur_stdev)
        cur_position = self.df.loc[self.df.index[-1], 'position'] + cur_signal
        cur_pnl = self.df.loc[self.df.index[-1], 'pnl'] + self.df.loc[self.df.index[-1], 'position'] * (price - self.df.loc[self.df.index[-1], 'price'])

        row[timestamp] = [price, cur_mean, cur_stdev, cur_signal, cur_signal, cur_pnl]
        new_row = pd.DataFrame.from_dict(row, orient='index', columns=[
            'price', 'rollmean', 'rollstdev', 'signal', 'position', 'pnl'])
        self.df = pd.concat([self.df, new_row])

        cur_prices = self.prices
        cur_prices[str(timestamp)] = price
        
        self.prices = cur_prices
        self.latest_ts = str(timestamp)
        self.latest_price = price
        self.latest_signal = cur_signal
                
    def cur_signal(self):
        return self.latest_signal

    def cur_price(self):
        return self.latest_price

    def get_ticker(self):
        return self.ticker
    
    def output_pnl_file(self):
        headers = ['price', 'signal', 'pnl']
        data = [self.df['price'], self.df['signal'], self.df['pnl']]
        pnl_df = pd.concat(data, axis=1, keys=headers)
        pnl_df.insert(loc = 0, column='datetime', value=self.df.index)

        pnl_df.to_csv('out/' + self.ticker+'_result.csv', index=False)
        
        return 0

    def output_price_file(self):
        headers = ['price']
        data = [self.df['price']]
        price_df = pd.concat(data, axis=1, keys=headers[-1:])
        price_df.insert(loc=0, column='datetime', value=self.df.index)

        price_df.to_csv('out/' + self.ticker+'_price.csv', index=False)
        
        return 0

    def get_price_at(self, time):

        # if time stored
        if time in self.prices:
            return self.prices[time]
        else:

            # look back through time
            interval = int(re.search(r'\d+', self.interval).group())
            timestamp = pd.to_datetime(time)
            
            times_list = [timestamp - timedelta(minutes=x) for x in range(0, interval)]
            for times in times_list:
                if str(time) in self.prices:
                    return self.prices[str(time)]

            # try 4pm for last 5 days
            times_list = [timestamp.floor('D') - timedelta(days=x) + timedelta(hours=16) for x in range(0, interval)]
            for times in times_list:
                if str(time) in self.prices:
                    return self.prices[str(time)]

            # not in stored data - try querying again
            return -1

    def get_signal_at(self, time):

        # if time stored
        if time in self.prices:
            return self.df.loc[time]['signal']
        else:

            # look back through time
            interval = int(re.search(r'\d+', self.interval).group())
            timestamp = pd.to_datetime(time)
            
            times_list = [timestamp - timedelta(minutes=x) for x in range(0, interval)]
            for times in times_list:
                if str(time) in self.prices:
                    return self.df.loc[time]['signal']

            # try 4pm for last 5 days
            times_list = [timestamp.floor('D') - timedelta(days=x) + timedelta(hours=16) for x in range(0, interval)]
            for times in times_list:
                if str(time) in self.prices:
                    return self.df.loc[time]['signal']

            # not in stored data - no signal
            return -1

    def get_prices(self):
        return self.prices

