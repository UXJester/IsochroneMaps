from dotenv import load_dotenv
import os
import openrouteservice
from openrouteservice.isochrones import isochrones
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

# Load environment variables from .env file
load_dotenv()

# Retrieve API key from environment variable
api_key = os.getenv("ORS_API_KEY")
if not api_key:
    raise ValueError(
        "API key not found. Please set the ORS_API_KEY environment variable in the .env file."
    )

# Initialize the client with the API key
client = openrouteservice.Client(key=api_key)

# Load the cities.csv file
csv_file = "data/location/geocoded_cities.csv"
if not os.path.exists(csv_file):
    raise FileNotFoundError(f"The file '{csv_file}' was not found.")

df = pd.read_csv(csv_file)

# Ensure the file has at least one row
if len(df) < 1:
    raise ValueError(f"The file '{csv_file}' must have at least one row.")

# Extract coordinates for each city
coords_list = []
for index, row in df.iterrows():
    city_name = row["City"].replace(" ", "").replace("/", "_")  # Sanitized city name
    latitude = row["Latitude"]
    longitude = row["Longitude"]

    if pd.isna(latitude) or pd.isna(longitude):
        raise ValueError(
            f"The row {index + 1} of '{csv_file}' has missing coordinates."
        )

    coords_list.append(
        [longitude, latitude]
    )  # OpenRouteService expects [longitude, latitude]


# Function to generate isochrones for a single city
def generate_isochrone(client, longitude, latitude, city_name):
    try:
        isochrone_result = isochrones(
            client,
            locations=[[longitude, latitude]],  # [longitude, latitude]
            profile="driving-car",  # Profile can be 'driving-car', 'cycling-regular', etc.
            range=[
                3600,  # Travel times in seconds (60 min), add more to the range for more options e.g. 1800 for 30 min
            ],
            range_type="time",  # Can be 'time' or 'distance'
            smoothing=25,  # Optional: smooth the isochrones
        )
        print(f"Generated isochrones for {city_name} successfully.")
        return city_name, isochrone_result
    except Exception as e:
        print(f"Error generating isochrones for {city_name}: {e}")
        return city_name, None
    finally:
        # Optional: Sleep to avoid hitting API rate limits
        sleep(1.5)  # Adjust the sleep time based on your API rate limit


# Parallelize the isochrone generation
isochrones_data = {}
with ThreadPoolExecutor(
    max_workers=2
) as executor:  # Adjust max_workers based on your system
    future_to_city = {
        executor.submit(
            generate_isochrone,
            client,
            longitude,
            latitude,
            df.iloc[index]["City"].replace(" ", "").replace("/", "_"),
        ): index
        for index, (longitude, latitude) in enumerate(coords_list)
    }

    for future in as_completed(future_to_city):
        city_name, isochrone_result = future.result()
        if isochrone_result:
            isochrones_data[city_name] = isochrone_result

# Save individual isochrones to GeoJSON files
for city_name, isochrone_result in isochrones_data.items():
    output_file = f"data/isochrones/{city_name}_isochrones.geojson"
    try:
        with open(output_file, "w") as f:
            json.dump(isochrone_result, f)
        print(f"Saved isochrones for {city_name} to {output_file}.")
    except Exception as e:
        print(f"Error saving isochrones for {city_name}: {e}")

# Save all isochrones data to a single GeoJSON file
output_file = "data/isochrones/isochrones.geojson"
try:
    with open(output_file, "w") as f:
        # Combine all isochrones into a single GeoJSON FeatureCollection
        combined_isochrones = {"type": "FeatureCollection", "features": []}
        for city_name, result in isochrones_data.items():
            for feature in result["features"]:
                # Add city name to properties for identification
                feature["properties"]["city"] = city_name
                combined_isochrones["features"].append(feature)

        json.dump(combined_isochrones, f)
    print(f"Saved all isochrones to {output_file}.")
except Exception as e:
    print(f"Error saving all isochrones: {e}")
