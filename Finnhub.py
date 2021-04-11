import requests
import json

from Ticker import Ticker

class FinnHub(object):

    _FINNHUB_URL = 'https://finnhub.io/api/v1/'

    def __init__(self, key=None):
        self.key = key
    
    def get(self, f, params):

        params['token'] = self.key

        response = requests.get(url=FinnHub._FINNHUB_URL+f, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            return -1