# Isochrone Maps

Isochrone Maps is a Python-based project designed to generate isochrone maps, which visualize areas reachable within a certain time or distance from a specific location. This project is useful for geospatial analysis, urban planning, and accessibility studies.

## Features

- Generate isochrone maps based on geospatial data.
- Debug Python scripts using the provided VS Code configuration.

## Prerequisites

- Python 3.x installed on your system.
- Visual Studio Code with the Python extension installed.
- An API key from [OpenRouteService](https://openrouteservice.org/).

### Obtaining an OpenRouteService API Key

1. Go to [OpenRouteService](https://openrouteservice.org/).
2. Sign up for a free account or log in if you already have one.
3. Navigate to the "API Keys" section in your account dashboard.
4. Create a new API key and copy it for later use.

## Setup

Setup can be preformed manually using the steps below, or can be executed by running `python3 setup_env.py` after cloning Step 1

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd IsochroneMaps
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Open the project in Visual Studio Code:
   ```bash
   code .
   ```

## Usage

The project incudes three Python scipts that should be run sequentially to generate the final Isochrone Maps
as well as two location CSV files used to create map layers. `cities.csv` lists cities and is the primary data source to generate the `isochrone` layer. `poi.csv` contains full address information for points of interest and the primary data source to generate the `Points of Interest` layer.

### CSV Data Analysis (Step 1)

Decide the central locations that require isochrones (e.g. cities) and the associated Points of Interest to be viewed
in relation to those locations. Location data is stored in `/data/location`.

1. Review `cities.csv` and `poi.csv` to ensure Comma-Separated Values (CSV) data is formatted correctly. Read [RFC 4180](https://datatracker.ietf.org/doc/html/rfc4180) for more information on the common format and MIME Type for CSV files.
2. Update the CSV files with different geographic data as needed. Ensure data provided follows the data shape in respective CSV as malformed data will cause errors in the Python scripts.

### Geocoding Locations (Step 2) `geocode.py`

Geocoding is the process of converting addresses or place names into geographic coordinates (latitude and longitude) that can be used to place markers on a map or perform spatial analysis. This project uses the `Nominatim` geocoder

1. Run `geocode.py` to geocode location data and generate `geocoded_*.csv` files stored in `/data/location`
2. It's common for the Nominatim service to return `timeout` and `location not found` errors. Errors will be logged to the console as well as the `Error` column in the CSV. If there are errors, geocode.py can be run again to update records with `timeout` errors.
3. For `location not found` errors, it's recommended to use a web service like [Nominatim](https://nominatim.openstreetmap.org/ui/search.html) to find and manually update latitude and longitude values.
4. Once geocoding is complete geocoder.py will return `All records are geocoded`

_Note:_ `geocode` and `process_geocoding` functions are used to geocode data. Additional data can be configured and processed using the patterns found under `# Process ...` comments at the bottom of `geocode.py`.
Adding additional data sets to be geocoded by `geocode.py` have not been tested at this time and may require refactor.

### Generating Isochrones (Step 3) `isochrone.py`

Isochrones are polygons that represent areas reachable within a specific time or distance from a central point. They are commonly used in transportation, urban planning, and accessibility analysis to visualize travel times or distances.

1. Run `isochrone.py` to generate isochrone polygons for the geocoded locations.
   This script uses the OpenRouteService API to calculate isochrones based on the provided API key.
   Sign up for an OpenRoute Service API key at https://openrouteservice.org/sign-up/
2. The output is stored as [GeoJSON](https://geojson.org/) files in the `/data/isochrones` directory. [RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946) provides more information on the GeoJSON format
3. Review the generated GeoJSON files to ensure accuracy. These files can be visualized using GIS tools or web mapping libraries.
   In this project GeoJSON files are used to visualize isochrones in the maps generated in the next step.

_Note:_ GeoJSON files are generated for each city then combined as `isochrones.geojson` used in the next step.
Individual `[city_name]_isochroes.geojson` can be used to add additional layers to the map, but not used at this time.

### Generating the Maps (Step 4) `maps.py`

`maps.py` generates HTML files to visualize isochrones and locations on a map. `maps.py` uses [Folium](https://python-visualization.github.io/folium/latest/index.html), [Leafletjs](https://leafletjs.com/), and [OpenStreetMap](https://www.openstreetmap.org)

1. Run `maps.py` and observe the maps generated are saved to `/maps/*_map.html`
2. Generated maps will display an OpenStreetMap with zoom, draw, and layer controls that visualize isochrones, locations, and map scale.

### Demo Map

[View the POI Map](https://uxjester.github.io/IsochroneMaps/poi_map.html)

_Note:_ `maps.py` can be updated to use different map tiles, additional layers, marker icons, etc. See documentation for [Folium](https://python-visualization.github.io/folium/latest/user_guide.html) and [Leafletjs](https://leafletjs.com/reference.html) for more information. Automated configuration is not supported at this time.

## Debugging

To debug Python scripts in this project, follow these steps:

1. Open a terminal and navigate to the project directory:

   ```bash
   cd /path/to/IsochroneMaps
   ```

2. Ensure the virtual environment is activated:

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. Run the Python script you want to debug with the `-m pdb` flag to enable the Python debugger:

   ```bash
   python -m pdb script_name.py
   ```

4. Use the debugger commands to step through the code, inspect variables, and troubleshoot issues. For example:
   - `n`: Execute the next line of code.
   - `c`: Continue execution until the next breakpoint.
   - `q`: Quit the debugger.

Refer to the [Python Debugger Documentation](https://docs.python.org/3/library/pdb.html) for more details on using the debugger.
VS Code was used to develop this project. Refer to [Python debugging in VS Code](https://code.visualstudio.com/docs/python/debugging) to configure debugging this project in VS Code

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
