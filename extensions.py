import requests

class APIException(Exception):
    pass


class CurrencyConverter:
    def __init__(self, API_KEY):
        self.API_KEY = API_KEY
        self.cache = {'cryptos': []}

    def get_cryptos_from_api(self):
        if self.cache['cryptos']:
            return self.cache['cryptos']
        base_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.API_KEY,
        }
        response = requests.get(base_url, headers=headers)
        data = response.json()
        data = data['data'][:10]
        excluded_cryptos = ['Tether USDt', 'USD Coin', 'TRON']
        cryptos = [crypto for crypto in data if crypto['name'] not in excluded_cryptos]
        self.cache['cryptos'] = cryptos
        return cryptos

    def get_currency_rate(self, crypto_currency, target_currency):
        key = '{0}'.format(crypto_currency)
        if key not in self.cache:
            base_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': self.API_KEY,
            }
            parameters = {
                'symbol': key,
                'convert': target_currency.upper()
            }
            response = requests.get(base_url, headers=headers, params=parameters)
            data = response.json()
            self.cache[key] = data['data'][key]['quote'][target_currency.upper()]['price']
        return self.cache[key]
