import requests
import csv
import os

def fetch_weather(location: str,
                  is_day: bool | None = None,
                  cloudy: bool | None = None):
    """
    Fetch weather data from Open-Meteo.

    Parameters
    ----------
    location : str
        City name (e.g. "London")

    is_day : bool | None
        True  -> force daytime
        False -> force nighttime
        None  -> use API value

    cloudy : bool | None
        True  -> force 100% cloud cover
        False -> force 0% cloud cover
        None  -> use API value

    Returns
    -------
    dict
    """

    # Geocode the city
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": location,
            "count": 1
        }
    ).json()

    if "results" not in geo:
        raise ValueError("Location not found.")

    latitude = geo["results"][0]["latitude"]
    longitude = geo["results"][0]["longitude"]

    # Fetch current weather
    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m",
                "cloud_cover",
                "is_day",
                "wind_speed_10m",
                "shortwave_radiation"
            ]
        }
    ).json()["current"]

    # Optional toggles to override API values
    if cloudy is not None:
        weather["cloud_cover"] = 100 if cloudy else 0

    if is_day is not None:
        weather["is_day"] = 1 if is_day else 0

    return weather


def log_weather(weather: dict,
                location: str,
                filename: str):
    """
    Append a weather sample to a CSV file.

    Parameters
    ----------
    weather : dict
        Dictionary returned by fetch_weather()

    location : str
        Name of the location

    filename : str
        CSV file to append to
    """

    file_exists = os.path.isfile(filename)

    fieldnames = [
        "location",
        "temperature_2m",
        "cloud_cover",
        "is_day",
        "wind_speed_10m",
        "shortwave_radiation"
    ]

    with open(filename, "a", newline="") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "location": location,
            "temperature_2m": weather["temperature_2m"],
            "cloud_cover": weather["cloud_cover"],
            "is_day": weather["is_day"],
            "wind_speed_10m": weather["wind_speed_10m"],
            "shortwave_radiation": weather["shortwave_radiation"]
        })