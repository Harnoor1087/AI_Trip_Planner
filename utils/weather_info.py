import requests

class WeatherForecastTool:
    def __init__(self, api_key:str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_current_weather(self, place:str):
        """Get current weather of a place"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": place,
                "appid": self.api_key,
            }
            response = requests.get(url, params=params, timeout=(3, 10))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise RuntimeError(f"weather request failed for {place}") from error
    
    def get_forecast_weather(self, place:str):
        """Get weather forecast of a place"""
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": place,
                "appid": self.api_key,
                "cnt": 10,
                "units": "metric"
            }
            response = requests.get(url, params=params, timeout=(3, 10))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            raise RuntimeError(f"weather forecast request failed for {place}") from error