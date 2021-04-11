import numpy as np
import pandas as pd
import os

from time import sleep
from threading import Thread
from Ticker import Ticker
from AlphaVantage import AlphaVantage
from Finnhub import FinnHub

ALPHAVANTAGE_API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")

class Server(object):
    def __init__(self, ticker_list, minutes, reload_file=None):

        # self properties
        self.interval = minutes
        self.tickers = {}
        self.last_updated = pd.Timestamp.now().floor('min')

        # currently only reload one file for one ticker is supported
        if reload_file:
            self.load_from_file(reload_file, ticker_list)
        else:    
            self.download_tickers(ticker_list)
        
        # creates and starts another thread to download market data asynchronously
        download_thread = Thread(target=self.thread_download)
        download_thread.daemon = True
        download_thread.start()

    def load_from_file(self, reload_file, ticker_list):

            ticker_prices = {}

            f = open(reload_file)

            for line in f:
                line = line.strip('\n')
                row = line.split(',')
                
                if row[0] != 'time':
                    ticker_prices[row[0]] = float(row[4])
            
            # currently only load historical data from file for one ticker is supported
            ticker = ticker_list[0]
            
            # creates pnl/price files after creating ticket object
            ticker_data = Ticker(ticker, self.interval, ticker_prices)
            ticker_data.output_pnl_file()
            ticker_data.output_price_file()

            self.tickers[ticker] = ticker_data
        

    def thread_download(self):
        while True:
            self.download_live()
            sleep(self.interval * 60)
        
    def get_price_at(self, datetime):

        prices = {}

        # returns dict of all tickers and their price
        for ticker in self.tickers.values():
            if datetime == 'now':
                price = ticker.cur_price()
            else:
                price = ticker.get_price_at(datetime)
            
            symbol = ticker.get_ticker()
            prices[symbol] = price

        return prices
    
    def get_signal_at(self, datetime):
        
        signals = {}

        # returns dict of all tickers and their signal
        for ticker in self.tickers.values():
            if datetime == 'now':
                signal = ticker.cur_signal()
            else:
                signal = ticker.get_signal_at(datetime)

            symbol = ticker.get_ticker()
            signals[symbol] = signal

        return signals
    
    def delete_ticker(self, ticker):

        serv_tickers = self.tickers

        # pops specified ticker from ticker dict
        if ticker in serv_tickers:
            serv_tickers.pop(ticker)
            self.tickers = serv_tickers
            return 0
        else:
            return 2
    
    def download_tickers(self, ticker_list):

        alpha = AlphaVantage(key=ALPHAVANTAGE_API_KEY)

        # time series intraday
        ## only pulling for past one month intra-day historical data

        function = 'TIME_SERIES_INTRADAY_EXTENDED'
        datatype = 'json'
        slice_ = 'year1month1'
        interval = str(self.interval) + 'min'

        for ticker in ticker_list:
            
            ticker_prices = {}
            params = {
                'function': function,
                'symbol': ticker,
                'interval': interval,
                'slice': slice_,
                'datatype': datatype,
                'apikey': ALPHAVANTAGE_API_KEY
            }

            response = alpha.get(params)

            if response == -1:
                return 2

            # only use close price per time interval
            for timestamp, prices in response.items():
                ticker_prices[timestamp] = float(prices[3])
            
            # creates a Ticker object with the prices
            ticker_data = Ticker(ticker, interval, ticker_prices)

            # creates pnl and price file for each ticker
            ticker_data.output_pnl_file()
            ticker_data.output_price_file()

            self.tickers[ticker] = ticker_data
        
        return 0
    
    def download_live(self):

        finnhub = FinnHub(key=FINNHUB_API_KEY)

        # download live quote data from FinnHub
        for ticker in self.tickers.values():

            # current quote
            function = 'quote'
            symbol = ticker.get_ticker()
            
            params = {
                'symbol': symbol
            }

            response = finnhub.get(function, params)
            cur_price = response['c']
            cur_time = str(pd.Timestamp.now().floor('min'))

            ticker.add_price(cur_time, cur_price)

        print("Downloading live for tickers")
        
        self.last_updated = pd.Timestamp.now().floor('min')

        return 0
    
    def get_last_updated(self):

        return self.last_updated
