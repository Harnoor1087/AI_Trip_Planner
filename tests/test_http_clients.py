from unittest.mock import Mock, patch

import pytest
import requests

from utils.currency_convertor import CurrencyConverter
from utils.weather_info import WeatherForecastTool


def test_weather_client_uses_timeout_and_raises_for_http_errors():
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("bad response")
    client = WeatherForecastTool("weather-key")

    with patch("utils.weather_info.requests.get", return_value=response) as request:
        with pytest.raises(RuntimeError, match="weather request failed"):
            client.get_current_weather("Goa")

    request.assert_called_once_with(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": "Goa", "appid": "weather-key"},
        timeout=(3, 10),
    )


def test_currency_client_normalizes_codes_and_uses_timeout():
    response = Mock()
    response.json.return_value = {"conversion_rates": {"EUR": 0.9}}
    client = CurrencyConverter("exchange-key")

    with patch("utils.currency_convertor.requests.get", return_value=response) as request:
        assert client.convert(100, " usd ", "eur") == 90

    request.assert_called_once_with(
        "https://v6.exchangerate-api.com/v6/exchange-key/latest/USD",
        timeout=(3, 10),
    )


def test_currency_client_rejects_missing_key_and_negative_amount():
    with pytest.raises(ValueError, match="API_KEY"):
        CurrencyConverter("")

    with pytest.raises(ValueError, match="negative"):
        CurrencyConverter("exchange-key").convert(-1, "USD", "EUR")