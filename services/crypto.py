import requests
import requests
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime


def get_price_history(symbol='bitcoin', currency='usd', days=7):
    url = f'https://api.coingecko.com/api/v3/coins/{symbol}/market_chart'
    params = {'vs_currency': currency, 'days': days}
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()

    # Цены в формате [timestamp, price]
    return [(x[0], x[1]) for x in data['prices']]


def generate_price_chart(symbol='bitcoin', currency='usd'):
    history = get_price_history(symbol, currency)

    timestamps = [datetime.fromtimestamp(ts / 1000).strftime('%b %d') for ts, _ in history]
    prices = [price for _, price in history]

    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, prices, label=f"{symbol.upper()} price", color='blue')
    plt.xticks(rotation=45)
    plt.title(f"{symbol.upper()} Price (Last 7 days)")
    plt.xlabel("Date")
    plt.ylabel(f"Price in {currency.upper()}")
    plt.tight_layout()
    plt.grid(True)
    plt.legend()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    return buf

API_URL = "https://api.coingecko.com/api/v3/simple/price"

def get_price_chart_url(symbol='bitcoin', currency='usd'):
    base_url = "https://quickchart.io/chart"
    chart_config = {
        "type": "line",
        "data": {
            "labels": [f"t-{i}" for i in range(10, 0, -1)],
            "datasets": [{
                "label": f"{symbol.upper()} price",
                "data": [100 + i*2 for i in range(10)],  # Фейковые данные для примера
            }]
        }
    }

    import json
    from urllib.parse import quote
    config_encoded = quote(json.dumps(chart_config))
    return f"{base_url}?c={config_encoded}"

def get_token_description(symbol='bitcoin', lang='en'):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}"
    res = requests.get(url, params={"localization": "true"})
    res.raise_for_status()
    data = res.json()

    description = data.get("description", {}).get(lang) or "Описание недоступно."
    # Ограничим размер описания
    return description.strip()[:1000] + '...'

def get_crypto_price(symbols=('bitcoin', 'ethereum', 'tether'), currency='usd'):
    symbols_str = ','.join(symbols)
    response = requests.get(API_URL, params={'ids': symbols_str, 'vs_currencies': currency})
    data = response.json()

    result = []
    for symbol in symbols:
        price = data.get(symbol, {}).get(currency)
        if price:
            result.append(f"{symbol.title()}: {price} {currency.upper()}")
    return '\n'.join(result)