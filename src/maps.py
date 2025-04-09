# Standard library imports
import os
import sys
from math import atan2, cos, degrees, radians, sin, sqrt
import re

# Third-party imports
import folium
import geojson
import pandas as pd
from folium import MacroElement
from folium.plugins import Draw
from jinja2 import Template
from jsmin import jsmin
from csscompressor import compress
import htmlmin


# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Local application imports
from config import IMAGES, ISOCHRONES, LOCATIONS, MAPS

# Load isochrone data from isochrones.geojson
if not os.path.exists(f"{ISOCHRONES}/isochrones.geojson"):
    raise FileNotFoundError("The file 'isochrones.geojson' was not found.")
with open(f"{ISOCHRONES}/isochrones.geojson") as f:
    isochrones_data = geojson.load(f)

# Load Cities Data
if not os.path.exists(f"{LOCATIONS}/geocoded_cities.csv"):
    raise FileNotFoundError("The file 'cities.csv' was not found.")
cities_df = pd.read_csv(f"{LOCATIONS}/geocoded_cities.csv")
if cities_df.empty:
    raise ValueError("The cities.csv file is empty.")


# Function to calculate the geographic midpoint
def calculate_geographic_midpoint(coords):
    if not coords:
        raise ValueError("No valid coordinates provided.")

    x, y, z = 0, 0, 0
    for lat, lon in coords:
        lat_rad = radians(lat)
        lon_rad = radians(lon)
        x += cos(lat_rad) * cos(lon_rad)
        y += cos(lat_rad) * sin(lon_rad)
        z += sin(lat_rad)

    total = len(coords)
    x /= total
    y /= total
    z /= total

    lon_mid = atan2(y, x)
    hyp = sqrt(x * x + y * y)
    lat_mid = atan2(z, hyp)

    return [degrees(lat_mid), degrees(lon_mid)]


# Extract valid coordinates from the DataFrame
if "Latitude" in cities_df.columns and "Longitude" in cities_df.columns:
    city_coords = cities_df.dropna(subset=["Latitude", "Longitude"])
    if city_coords.empty:
        raise ValueError("No valid city coordinates found.")
    coords = list(zip(city_coords["Latitude"], city_coords["Longitude"]))
    map_center = calculate_geographic_midpoint(coords)
else:
    raise ValueError("Cities data must contain 'Latitude' and 'Longitude' columns.")

# Define Colors
colors = ["orange", "red", "blue", "green", "purple", "gray"]

# Create a dictionary to map city names to colors
city_colors = {}

# Dynamically assign unique colors to city isochrones
city = {
    feature["properties"].get("city", "Unknown")
    for feature in isochrones_data["features"]
}
for idx, city in enumerate(city):
    city_colors[city] = colors[idx % len(colors)]


# Function to create a map with layers
def create_map(include_poi=False):
    m = folium.Map(location=map_center, zoom_start=8, control_scale=True)

    # Define layers
    draw_layer = folium.FeatureGroup(name="Draw Layer", show=True)
    isochrones_layer = folium.FeatureGroup(name="Isochrones", show=True)
    cities_layer = folium.FeatureGroup(name="Cities", show=True)
    poi_layer = folium.FeatureGroup(name="Points of Interest", show=include_poi)

    # TODO: Add layers for different time intervals layers below are placeholders and not used
    thirty_min_layer = folium.FeatureGroup(name="30 Minutes", show=False)
    sixty_min_layer = folium.FeatureGroup(name="60 Minutes", show=False)

    # Add isochrones to map layer. Reversed to render shorter isochrones on top to prevent overlapping
    for feature in reversed(isochrones_data["features"]):
        city_name = feature["properties"].get("city", "Unknown")
        value = feature["properties"].get("value", 0)
        label = f"{value // 60} minutes" if value else "Unknown"

        folium.GeoJson(
            feature,
            style_function=lambda feature: {
                "fillColor": city_colors.get(
                    feature["properties"].get("city", "Unknown"), "gray"
                ),  # Dynamically get the color based on the city name
                "color": city_colors.get(
                    feature["properties"].get("city", "Unknown"), "gray"
                ),  # Border color matches the fill color
                "weight": 2,
                "fillOpacity": 0.4,
            },
            tooltip=folium.Tooltip(f"Isochrone for {city_name}: {label}"),
        ).add_to(isochrones_layer)

        # TODO : Add individual isochrones to specific layers based on time to better organize and visualize

    # Add city markers and labels
    for _, row in city_coords.iterrows():
        city_name = row["City"] if pd.notna(row["City"]) else "Unknown"

        if pd.isna(row["Latitude"]) or pd.isna(row["Longitude"]):
            print(f"Error: Missing coordinates for city '{city_name}'. Skipping...")
            continue

        latitude = row["Latitude"]
        longitude = row["Longitude"]

        # Add City Markers with popup and tooltip
        folium.Marker(
            location=[latitude, longitude],
            popup=folium.Popup(f"<b>{city_name}</b>", max_width=300),
            icon=folium.Icon(color="red", icon="tower"),
            tooltip=folium.Tooltip(
                f"{city_name}",
                permanent=True,
                sticky=False,
                direction="top",
                offset=(0, -32),
                show=True,
            ),
        ).add_to(cities_layer)

    # Add poi markers (if enabled)
    if include_poi:
        geocoded_file = f"{LOCATIONS}/geocoded_poi.csv"
        if not os.path.exists(geocoded_file):
            raise FileNotFoundError(f"The file '{geocoded_file}' was not found.")
        poi_df = pd.read_csv(geocoded_file)
        if poi_df.empty:
            raise ValueError("The geocoded_poi.csv file is empty.")

        for _, row in poi_df.iterrows():
            poi_name = row["POIName"] if pd.notna(row["POIName"]) else "Unknown"
            poi_city = row["City"] if pd.notna(row["City"]) else "Unknown"
            latitude = row["Latitude"] if pd.notna(row["Latitude"]) else None
            longitude = row["Longitude"] if pd.notna(row["Longitude"]) else None

            if latitude is None or longitude is None:
                print(
                    f"Error: Missing coordinates for Point of Interest '{poi_name}'. Skipping..."
                )
                continue

            # Add POI Markers with popup and tooltip. To use a custom icon use folium.CustomIcon
            folium.Marker(
                location=[latitude, longitude],
                popup=folium.Popup(
                    f"<b>{poi_name}</b><br>City: {poi_city}",
                    max_width=300,
                ),
                icon=folium.Icon(color="blue", icon="camera"),
                tooltip=folium.Tooltip(
                    f"{poi_name}",
                    sticky=True,
                    direction="top",
                    show=True,
                ),
            ).add_to(poi_layer)

    # Add layers to the map. Draw layer is added to allow user to draw on the map and edit drawn features
    draw_layer.add_to(m)
    isochrones_layer.add_to(m)
    cities_layer.add_to(m)
    if include_poi:
        poi_layer.add_to(m)

    # Add layer control to toggle layers
    folium.LayerControl(collapsed=True).add_to(m)

    # Define Draw Options
    draw_cnfg = {
        "metric": False,  # Disable metric units
        "feet": False,  # Disable feet
        "nauticalmiles": False,  # Disable nautical miles
    }

    # Add Draw tools
    Draw(
        export=True,
        show_geometry_on_click=False,
        feature_group=draw_layer,
        edit_options={"featureGroup": "editLayer"},
        draw_options={
            "polyline": {
                **draw_cnfg,
                "showLength": True,
            },
            "polygon": {**draw_cnfg, "showArea": True},
            "rectangle": {**draw_cnfg, "showArea": True},
            "circle": {**draw_cnfg, "showRadius": True, "shapeOptions": {}},
        },
    ).add_to(m)

    # Read the contents of map_config.js
    js_file_path = os.path.join(os.path.dirname(__file__), "static/js/map_config.js")
    with open(js_file_path, "r") as js_file:
        map_config_js = js_file.read()
        minified_js = jsmin(map_config_js)

    # Add a custom script to configure the map
    el = MacroElement().add_to(m)
    el._template = Template(
        f"""
        {{% macro script(this, kwargs) %}}
        const map = {m.get_name()};
        {map_config_js}
        {{% endmacro %}}
        """
    )

    # Add custom CSS for the map
    css_file_path = os.path.join(os.path.dirname(__file__), "static/css/map_styles.css")
    with open(css_file_path, "r") as css_file:
        map_css = css_file.read()
        minified_css = compress(map_css)

    styles = MacroElement().add_to(m)
    styles._template = Template(
        f"""
        {{% macro header(this, kwargs) %}}
        <style>
          {map_css}
        </style>
        {{% endmacro %}}
        """
    )

    return m


def minify_html(file_path):
    with open(file_path, "r") as file:
        html_content = file.read()

    # Minify <script> tags
    def minify_script(match):
        script_content = match.group(1)
        minified_script = jsmin(script_content, quote_chars="'\"")
        return f"<script>{minified_script}</script>"

    html_content = re.sub(
        r"<script>(.*?)</script>", minify_script, html_content, flags=re.DOTALL
    )

    # Minify <style> tags
    def minify_style(match):
        style_content = match.group(1)
        minified_style = compress(style_content)
        return f"<style>{minified_style}</style>"

    html_content = re.sub(
        r"<style>(.*?)</style>", minify_style, html_content, flags=re.DOTALL
    )

    # Minify the entire HTML, but avoid removing spaces in strings
    minified_html = htmlmin.minify(
        html_content,
        remove_comments=True,
        remove_empty_space=True,
        reduce_boolean_attributes=True,
        remove_optional_attribute_quotes=False,
    )

    with open(file_path, "w") as file:
        file.write(minified_html)


# Generate Maps using create_map function. Additional maps can be created by calling the function with different parameters
# Create maps directory if it doesn't exist
if not os.path.exists(MAPS):
    os.makedirs(MAPS)

# Generate test map to test JS generated by maps.py
# map_without_members = create_map(include_members=False)
# map_without_members.save(f"{MAPS}/test_gen.html")
# print("Map without members saved as 'test_gen.html'.")

# Generate the map without Points of Interest
map_without_poi = create_map(include_poi=False)
map_without_poi.save(f"{MAPS}/city_isochrone_map.html")
print("Map without poi saved as 'city_isochrone_map.html'.")

# Generate the map with Points of Interest
map_with_poi = create_map(include_poi=True)
map_with_poi.save(f"{MAPS}/poi_map.html")
map_with_poi.save("docs/poi_map.html")
print("Map with Points of Interest saved as 'poi_map.html'.")
