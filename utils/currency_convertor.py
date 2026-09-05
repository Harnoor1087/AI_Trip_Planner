import requests

class CurrencyConverter:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("EXCHANGE_RATE_API_KEY is required")
        self.base_url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest"
    
    def convert(self, amount:float, from_currency:str, to_currency:str):
        """Convert the amount from one currency to another"""
        if amount < 0:
            raise ValueError("amount must not be negative")
        from_currency = from_currency.strip().upper()
        to_currency = to_currency.strip().upper()
        if len(from_currency) != 3 or len(to_currency) != 3:
            raise ValueError("currencies must be three-letter ISO codes")
        response = requests.get(
            f"{self.base_url}/{from_currency}",
            timeout=(3, 10),
        )
        response.raise_for_status()
        payload = response.json()
        rates = payload.get("conversion_rates", {})
        if to_currency not in rates:
            raise ValueError(f"{to_currency} not found in exchange rates")
        return amount * rates[to_currency]