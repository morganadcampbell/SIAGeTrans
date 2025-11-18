from datetime import datetime
import openmeteo_requests
import requests_cache
from retry_requests import retry
from DatabaseController import DatabaseController
from models.databaseObject import DatabaseObject

class WeatherController:
    def __init__(self):
        self.__databaseController = DatabaseController()
        self.__cache_session = requests_cache.CachedSession('/files/.cache', expire_after = 3600)
        self.__retry_session = retry(self.__cache_session, retries = 5, backoff_factor = 0.2)
        self.__openmeteo = openmeteo_requests.Client(session = self.__retry_session)
        self.__url = "https://api.open-meteo.com/v1/forecast"
        self.__params = {
                            "latitude": -22.8833,
                            "longitude": -43.1036,
                            "current": "temperature_2m",
                            "timezone": "America/Sao_Paulo"
                        }

    def getCurrentTemperature(self, region : str, latitude : float, longitude : float) -> float:
        self.__params[latitude] = latitude
        self.__params[longitude] = longitude
        responses = self.__openmeteo.weather_api(self.__url, params=self.__params)
        current_temperature_2m = responses[0].Current().Variables(0).Value() # get current temperature
        data = {"ds_region": region,
                "dt_measurement": datetime.today().strftime('%Y-%m-%d'),
                "nr_temperature_c": current_temperature_2m}
        self.__databaseController.insert(DatabaseObject('weather_measurements', **data)) # insert data to Database
        return current_temperature_2m

    def getMaxAndMinTemperature(self, region : str) -> tuple[float]:
        query = f"select max(nr_temperature_c) as maximum, min(nr_temperature_c) as minimum from weather_measurements where ds_region = '{region}'"
        response = self.__databaseController.query(['maximum', 'minimum'], query)[0]
        return (response.maximum, response.minimum)
    