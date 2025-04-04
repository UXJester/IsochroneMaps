import folium
import geojson
import os
import pandas as pd
from folium import JsCode, Element
from folium.plugins import Draw, MeasureControl
from folium.plugins import GroupedLayerControl
from jinja2 import Template
from math import radians, degrees, sin, cos, atan2, sqrt

# Load isochrone data from isochrones.geojson
if not os.path.exists("data/isochrones/isochrones.geojson"):
    raise FileNotFoundError("The file 'isochrones.geojson' was not found.")
with open("data/isochrones/isochrones.geojson") as f:
    isochrones_data = geojson.load(f)

# Load Cities Data
if not os.path.exists("data/location/geocoded_cities.csv"):
    raise FileNotFoundError("The file 'cities.csv' was not found.")
cities_df = pd.read_csv("data/location/geocoded_cities.csv")
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

    # Create feature groups for layers
    draw_layer = folium.FeatureGroup(name="Draw Layer", show=True)
    isochrones_layer = folium.FeatureGroup(name="Isochrones", show=True)
    cities_layer = folium.FeatureGroup(name="Cities", show=True)
    poi_layer = folium.FeatureGroup(name="Points of Interest", show=include_poi)

    # TODO: Add layers for different time intervals
    thirty_min_layer = folium.FeatureGroup(name="30 Minutes", show=False)
    sixty_min_layer = folium.FeatureGroup(name="60 Minutes", show=False)

    # Add isochrones to the isochrones layer
    for feature in reversed(
        isochrones_data["features"]
    ):  # Reverse to render shorter isochrones on top
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

        # TODO : Add isochrones to specific layers based on time

    # Add city markers and labels to the cities layer
    for _, row in city_coords.iterrows():
        city_name = row["City"] if pd.notna(row["City"]) else "Unknown"

        if pd.isna(row["Latitude"]) or pd.isna(row["Longitude"]):
            print(f"Error: Missing coordinates for city '{city_name}'. Skipping...")
            continue

        latitude = row["Latitude"]
        longitude = row["Longitude"]

        # Add a marker for the city
        folium.Marker(
            location=[latitude, longitude],
            popup=folium.Popup(f"<b>{city_name}</b>", max_width=300),
            icon=folium.Icon(color="red", icon="tower"),
            tooltip=folium.Tooltip(
                f"{city_name}", sticky=True, direction="top", show=True
            ),
        ).add_to(cities_layer)

        # Add a label for the city
        folium.Marker(
            location=[latitude, longitude],
            icon=folium.DivIcon(
                html=f"""
                <div style="background-color: black; font-size: 9px; color: white; text-align: center; width: max-content; border-radius: 4px; padding: 2px 4px; position: absolute; top: -50px; left: -125%;">
                    <b>{city_name}</b>
                </div>
                """
            ),
        ).add_to(cities_layer)

    # Add poi markers to the poi layer (if enabled)
    if include_poi:
        geocoded_file = "data/location/geocoded_poi.csv"
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

            folium.Marker(
                location=[latitude, longitude],
                popup=folium.Popup(
                    f"<b>{poi_name}</b><br>City: {poi_city}",
                    max_width=300,
                ),
                icon=folium.Icon(
                    color="blue", icon="camera"
                ),  # Use folium.CustomIcon for custom icons
                tooltip=folium.Tooltip(
                    f"{poi_name}",
                    sticky=True,
                    direction="top",
                    show=True,
                ),
            ).add_to(poi_layer)

    # Add layers to the map
    draw_layer.add_to(m)
    isochrones_layer.add_to(m)
    cities_layer.add_to(m)
    if include_poi:
        poi_layer.add_to(m)

    # Add layer control and draw tools to toggle layers
    folium.LayerControl(collapsed=True).add_to(m)

    # Define Draw Options
    draw_cnfg = {
        "metric": False,  # Disable metric units
        "feet": False,  # Disable feet
        "nauticalmiles": False,  # Disable nautical miles
    }

    # Add Draw plugin with event listener
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

    el = folium.MacroElement().add_to(m)
    el._template = Template(
        """
    {% macro script(this, kwargs) %}
      // Haversine formula to calculate distance between two lat/lng points
      // Because L.GeometryUtil.geodesicLength() is not available in Leaflet
      // Reference: https://en.wikipedia.org/wiki/Haversine_formula
      function haversineDistance(latlngs) {
        const R = 6371000; // Radius of the Earth in meters
        let totalDistance = 0;

        for (let i = 0; i < latlngs.length - 1; i++) {
            const [lat1, lon1] = [latlngs[i].lat, latlngs[i].lng];
            const [lat2, lon2] = [latlngs[i + 1].lat, latlngs[i + 1].lng];

            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;

            const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                      Math.sin(dLon / 2) * Math.sin(dLon / 2);

            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
            totalDistance += R * c;
        }

        return totalDistance; // Distance in meters
      }

    {{ this._parent.get_name() }}.on(L.Draw.Event.CREATED, function(e){
        const layer = e.layer,
              type = e.layerType;

        // Conversion factors: multiply by these to convert to desired units
        // meters to miles = 1 / 1609.34 ≈ 0.000621371
        // m² (sq meters) to acres = 1 / 4046.8564224 ≈ 0.000247105
        if (type === 'polyline') {
            const latlngs = layer.getLatLngs();
            const length = haversineDistance(latlngs);
            const lengthInMiles = (length * 0.000621371).toFixed(2);  // Convert meters to miles
            layer.bindTooltip(`Length: ${lengthInMiles} miles`, {
                permanent: false,
                direction: 'top',
                offset: [0, -10]
            }).openTooltip();
        } else if (type === 'polygon' || type === 'rectangle') {
            // Calculate and display area in acres
            const area = L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
            const areaInAcres = (area * 0.000247105).toFixed(2);  // Convert m² to acres
            layer.bindTooltip(`Area: ${areaInAcres} acres`, {
                permanent: false,
                direction: 'top',
                offset: [0, -10]
            });
        } else if (type === 'circle') {
            // Calculate and display radius in miles
            const radiusInMiles = (layer.getRadius() * 0.000621371).toFixed(2);
            layer.bindTooltip(`Radius: ${radiusInMiles} miles`, {
                permanent: false,
                direction: 'top',
                offset: [0, -10]
            });
        } else if (type === 'marker') {
            // Display coordinates for markers
            const lat = layer.getLatLng().lat.toFixed(6);
            const lng = layer.getLatLng().lng.toFixed(6);
            layer.bindTooltip(`Coordinates: (${lat}, ${lng})`, {
                permanent: false,
                direction: 'top',
                offset: [0, 0]
            });
        }

        // Add the layer to the map
        {{ this._parent.get_name() }}.addLayer(layer);
    });

    {% endmacro %}
    """
    )

    # TODO: Add grouped layer control for better organization

    return m


# Generate the map without Points of Interest
map_without_poi = create_map(include_poi=False)
map_without_poi.save("maps/city_isochrone_map.html")
print("Map without poi saved as 'city_isochrone_map.html'.")

# Generate the map with Points of Interest
map_with_poi = create_map(include_poi=True)
map_with_poi.save("maps/poi_map.html")
print("Map with Points of Interest saved as 'poi_map.html'.")
