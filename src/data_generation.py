import math
import requests
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

filename = DATA_DIR / "solar_training_data.csv"


def fetch_open_meteo_weather(location, start_date, end_date):
    geo_res = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1}
    ).json()

    if "results" not in geo_res:
        raise ValueError(f"Location not found: {location}")

    place = geo_res["results"][0]
    lat = place["latitude"]
    lon = place["longitude"]

    weather_res = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": [
                "temperature_2m",
                "cloud_cover",
                "is_day",
                "wind_speed_10m",
                "shortwave_radiation",
                "direct_radiation",
                "diffuse_radiation"
            ],
            "timezone": "auto"
        }
    ).json()

    hourly = weather_res["hourly"]
    df = pd.DataFrame(hourly)

    df["location"] = location
    df["latitude"] = lat
    df["longitude"] = lon

    return df


def estimate_solar_angles(timestamp, latitude):
    """
    Simple approximation.
    Good enough for generating first training data.
    Later, replace this with pvlib for higher accuracy.
    """

    dt = pd.to_datetime(timestamp)

    hour = dt.hour + dt.minute / 60
    day_of_year = dt.dayofyear

    # Approximate solar declination
    declination = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))

    # Approximate hour angle
    hour_angle = 15 * (hour - 12)

    lat_rad = math.radians(latitude)
    dec_rad = math.radians(declination)
    h_rad = math.radians(hour_angle)

    altitude = math.degrees(
        math.asin(
            math.sin(lat_rad) * math.sin(dec_rad)
            + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(h_rad)
        )
    )

    # Basic azimuth approximation
    azimuth = 180 + hour_angle

    return max(0, altitude), azimuth % 360


def estimate_panel_power(row, tilt, azimuth, capacity_kwp):
    sun_altitude, sun_azimuth = estimate_solar_angles(
        row["time"],
        row["latitude"]
    )

    if row["is_day"] == 0 or sun_altitude <= 0:
        return 0.0

    direct = row.get("direct_radiation", 0)
    diffuse = row.get("diffuse_radiation", 0)

    # Convert angles to radians
    beta = math.radians(tilt)
    sun_alt = math.radians(sun_altitude)
    az_diff = math.radians(azimuth - sun_azimuth)

    # Approximate incidence angle
    cos_theta = (
        math.sin(sun_alt) * math.cos(beta)
        + math.cos(sun_alt) * math.sin(beta) * math.cos(az_diff)
    )

    cos_theta = max(0, cos_theta)

    # Direct + diffuse irradiance on tilted panel
    tilted_irradiance = (
        direct * cos_theta
        + diffuse * ((1 + math.cos(beta)) / 2)
    )

    # Convert W/m² style irradiance into approximate kW output
    power_kw = capacity_kwp * (tilted_irradiance / 1000)

    return max(0, power_kw)


import csv
import os


def generate_solar_training_csv(
    location,
    start_date,
    end_date,
    house_id,
    inverter_kw,
    arrays,
    filename=filename,
    tilt_range=range(0, 91, 10),
    azimuth_range=range(0, 360, 30)
):
    weather_df = fetch_open_meteo_weather(
        location,
        start_date,
        end_date
    )

    fieldnames = [
        "timestamp",
        "location",
        "house_id",
        "array_id",
        "latitude",
        "longitude",

        "inverter_kw",
        "installed_capacity_kwp",

        "temperature_2m",
        "cloud_cover",
        "is_day",
        "wind_speed_10m",
        "shortwave_radiation",
        "direct_radiation",
        "diffuse_radiation",

        "panel_tilt",
        "panel_azimuth",
        "energy_output_kw"
    ]

    file_exists = os.path.isfile(filename)

    with open(filename, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for _, weather in weather_df.iterrows():
            for array in arrays:
                for tilt in tilt_range:
                    for azimuth in azimuth_range:

                        power_kw = estimate_panel_power(
                            weather,
                            tilt,
                            azimuth,
                            array["capacity_kwp"]
                        )

                        writer.writerow({
                            "timestamp": weather["time"],
                            "location": location,
                            "house_id": house_id,
                            "array_id": array["array_id"],
                            "latitude": weather["latitude"],
                            "longitude": weather["longitude"],

                            "inverter_kw": inverter_kw,
                            "installed_capacity_kwp": array["capacity_kwp"],

                            "temperature_2m": weather["temperature_2m"],
                            "cloud_cover": weather["cloud_cover"],
                            "is_day": weather["is_day"],
                            "wind_speed_10m": weather["wind_speed_10m"],
                            "shortwave_radiation": weather["shortwave_radiation"],
                            "direct_radiation": weather["direct_radiation"],
                            "diffuse_radiation": weather["diffuse_radiation"],

                            "panel_tilt": tilt,
                            "panel_azimuth": azimuth,
                            "energy_output_kw": power_kw
                        })

    print(f"Finished writing data to {filename}")