# Standard library imports
import os
import webbrowser

# Third-party imports
import requests
import certifi
import geojson
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from jsonschema import validate, ValidationError

# GeoJSON schema for validation
GEOJSON_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "features": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "geometry": {"type": "object"},
                    "properties": {"type": "object"},
                },
                "required": ["type", "geometry", "properties"],
            },
        },
    },
    "required": ["type", "features"],
}

app = Flask(__name__)

CORS(app)

# Load environment variables from .env file
load_dotenv()

# Retrieve API key from environment variable
api_key = os.getenv("ORS_API_KEY")
if not api_key:
    raise ValueError(
        "API key not found. Please set the ORS_API_KEY environment variable in the .env file."
    )


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/maps/<path:filename>")
def maps(filename):
    # Serve any file from the "maps" directory
    return send_from_directory("maps", filename)


@app.route("/generate_isochrone", methods=["GET"])
def generate_isochrone():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    time = request.args.get("time", 60)  # Default to 60 minutes

    try:
        # Use OpenRouteService API to generate the isochrone
        url = "https://api.openrouteservice.org/v2/isochrones/driving-car"
        headers = {"Authorization": api_key}
        params = {
            "locations": [[float(lng), float(lat)]],
            "range": [int(time)],
            "smoothing": 25,
        }

        response = requests.post(
            url, json=params, headers=headers, verify=certifi.where()
        )
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Validate GeoJSON
        geojson_data = response.json()
        try:
            validate(instance=geojson_data, schema=GEOJSON_SCHEMA)
        except ValidationError as e:
            raise ValueError(f"Invalid GeoJSON object: {e.message}")

        return jsonify(geojson_data)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling OpenRouteService API: {e}")
        return (
            jsonify({"error": "Failed to generate isochrone", "details": str(e)}),
            500,
        )
    except ValueError as e:
        app.logger.error(f"GeoJSON validation error: {e}")
        return jsonify({"error": "Invalid GeoJSON object", "details": str(e)}), 500


if __name__ == "__main__":
    webbrowser.open("http://localhost:8000")
    app.run(debug=True, host="localhost", port=8000)
