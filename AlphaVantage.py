import requests
import json
import csv

from Ticker import Ticker

class AlphaVantage(object):

    _ALPHA_VANTAGE_URL = 'https://www.alphavantage.co/query?'

    def __init__(self, key=None, output_format='json'):
        self.key = key
        self.output_format = output_format

    def get(self, params):

        # grabs a csv file
        response = requests.get(url=AlphaVantage._ALPHA_VANTAGE_URL, params=params)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            data = csv.reader(content.splitlines(), delimiter=',')

            out = {}
            
            # return a dict
            for row in reversed(list(data)):
                if row[0] != 'time':
                    out[row[0]] = [row[1], row[2], row[3], row[4], row[5]]

            if len(out) == 0:
                return -1

            return out
        else:
            return -1


