import requests
import json
import csv

from Ticker import Ticker

ALPHA_LEGEND = "Meta Data"
ALPHA_API_INFO = "1. Information"
ALPHA_API_SYMBOL = "2. Symbol"
ALPHA_API_LAST_REFRESHED = "3. Last Refreshed"
ALPHA_API_INTERVAL = "4. Interval"
ALPHA_TIMESERIES = "Time Series"

class AlphaVantage(object):

    _ALPHA_VANTAGE_URL = 'https://www.alphavantage.co/query?'

    def __init__(self, key=None, output_format='json'):
        self.key = key
        self.output_format = output_format

    def get(self, params):
        response = requests.get(url=AlphaVantage._ALPHA_VANTAGE_URL, params=params)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            data = csv.reader(content.splitlines(), delimiter=',')

            out = {}

            for row in reversed(list(data)):
                if row[0] != 'time':
                    out[row[0]] = [row[1], row[2], row[3], row[4], row[5]]

            if len(out) == 0:
                return -1

            return out
        else:
            return -1


