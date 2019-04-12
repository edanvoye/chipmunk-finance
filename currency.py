
import requests
import datetime

class CurrencyCache():
    def __init__(self):
        self.date = datetime.date.today()
        self.currency_cache = {}
    def get(self, currency_from, currency_to):
        if datetime.date.today() != self.date:
            self.date = datetime.date.today()
            self.currency_cache = {}
        return self.currency_cache.get(currency_from + '_' + currency_to)
    def add(self, currency_from, currency_to, value):
        self.currency_cache[currency_from + '_' + currency_to] = value

currency_cache = CurrencyCache()

def currency_current_rate(currency_from, currency_to):
    if currency_from == currency_to:
        return 1.0

    value = currency_cache.get(currency_from, currency_to)
    if not value is None:
        return value

    url = 'https://api.ratesapi.io/api/latest?base=%s' % (currency_to)
    response = requests.get(url)

    if response.status_code==200:
        j = response.json()
        for c in j.get('rates'):
            currency_cache.add(c, currency_to, 1.0 / j.get('rates')[c])
        if currency_from in j.get('rates'):
            return 1.0 / j.get('rates')[currency_from]
    raise Exception('Error getting current exchange rate from %s to %s' % (currency_from, currency_to))

if __name__ == "__main__":

    # currency API tests

    for _ in range(2):
        for c1,base in [('USD','CAD'), ('CAD','USD'), ('CAD','EUR')]:
            print('Current rate 1.00 %s = %.2f %s' % (c1,currency_current_rate(c1,base),base))