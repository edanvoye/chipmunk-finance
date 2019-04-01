
import requests

# TODO cache
# TODO fct to get all rates for base_currency

def currency_current_rate(currency_from, currency_to):
    if currency_from == currency_to:
        return 1.0

    url = 'https://ratesapi.io/api/latest?base=%s&symbols=%s' % (currency_from, currency_to)
    response = requests.get(url)
    if response.status_code==200:
        j = response.json()
        if currency_to in j.get('rates'):
            return j.get('rates')[currency_to]
    raise Exception('Error getting current exchange rate from %s to %s' % (currency_from, currency_to))

if __name__ == "__main__":

    # currency API tests

    for c1,c2 in [('USD','CAD'), ('CAD','USD'), ('CAD','EUR')]:
        print('Current rate 1.00 %s = %.2f %s' % (c1,currency_current_rate(c1,c2),c2))