# Isochrone Maps

Isochrone Maps is a Python-based project designed to generate isochrone maps, which visualize areas reachable within a certain time or distance from a specific location. This project is useful for geospatial analysis, urban planning, and accessibility studies.

## Features

- Generate isochrone maps based on geospatial data.
- Debug Python scripts using the provided VS Code configuration.

## Prerequisites

- Python 3.x installed on your system.
- Visual Studio Code with the Python extension installed.

## Setup

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

## Debugging

The project includes a pre-configured VS Code debugging setup for Python scripts. To debug a specific Python file:

1. Open the `Run and Debug` panel in VS Code.
2. Select the `Launch geocode.py` configuration.
3. When prompted, enter the name of the Python file to debug (e.g., `geocode.py`).

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
