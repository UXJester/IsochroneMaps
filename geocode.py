from geopy.geocoders import Nominatim
import pandas as pd
import ssl
import certifi
import os

# Create a secure SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Initialize the geolocator with the SSL context
geolocator = Nominatim(user_agent="geo_mapper", ssl_context=ssl_context)


# Function to load and prepare data for geocoding
def load_data(file_path, dtype=None):
    if os.path.exists(file_path):
        return pd.read_csv(file_path, dtype=dtype)
    else:
        raise FileNotFoundError(f"{file_path} not found.")


# Function to geocode a single row
def geocode(address, city, state, zip_code):
    # Build the full address dynamically, skipping empty fields
    full_address = ", ".join(filter(None, [address, city, state, zip_code]))
    try:
        location = geolocator.geocode(full_address)
        return (
            (location.latitude, location.longitude, None)
            if location
            else (None, None, "Location not found")
        )
    except Exception as e:
        error_message = f"Error geocoding address '{full_address}': {e}"
        print(error_message)
        return (None, None, error_message)


# Function to process geocoding for a given DataFrame
def process_geocoding(df, output_file, columns_to_geocode):
    # Check if the output file already exists
    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file, dtype={"Zip": str})
        # Clear the error for rows with valid latitude and longitude
        existing_df.loc[
            existing_df["Latitude"].notna() & existing_df["Longitude"].notna(), "Error"
        ] = None

        # Identify rows that need to be geocoded (those with errors or missing coordinates)
        rows_to_process = existing_df[
            existing_df["Error"].notna()
            | existing_df["Latitude"].isna()
            | existing_df["Longitude"].isna()
        ]

        # Only include rows from the new data that are not already in the existing file
        new_rows = df[
            ~df[columns_to_geocode.keys()]
            .apply(tuple, axis=1)
            .isin(existing_df[columns_to_geocode.keys()].apply(tuple, axis=1))
        ]

        # Combine rows that need updates with new rows
        df_to_geocode = pd.concat([rows_to_process, new_rows]).drop_duplicates(
            subset=columns_to_geocode.keys(), keep="last"
        )
    else:
        df_to_geocode = df.copy()

    # Ensure the DataFrame has the required columns
    if "Latitude" not in df_to_geocode.columns:
        df_to_geocode["Latitude"] = None
    if "Longitude" not in df_to_geocode.columns:
        df_to_geocode["Longitude"] = None
    if "Error" not in df_to_geocode.columns:
        df_to_geocode["Error"] = None

    # Apply geocoding only to rows that need updates
    def safe_geocode(row):
        try:
            # Dynamically include Address if it exists in columns_to_geocode
            address = row.get(columns_to_geocode.get("Address", ""), "")
            city = row.get(columns_to_geocode["City"], "")
            state = row.get(columns_to_geocode["State"], "")
            zip_code = row.get(columns_to_geocode["Zip"], "")
            result = geocode(address, city, state, zip_code)
            # Ensure the result is always a tuple of three elements
            return pd.Series(
                result if len(result) == 3 else (None, None, "Invalid result")
            )
        except Exception as e:
            return pd.Series([None, None, f"Unexpected error: {e}"])

    # Apply the safe_geocode function only to rows that need updates
    rows_to_process = df_to_geocode[
        df_to_geocode["Latitude"].isna()
        | df_to_geocode["Longitude"].isna()
        | df_to_geocode["Error"].notna()
    ]

    if rows_to_process.empty:
        print("All records are geocoded")
        return

    geocoded_results = rows_to_process.apply(safe_geocode, axis=1)
    if len(geocoded_results.columns) == 3:  # Ensure the result has three columns
        rows_to_process[["Latitude", "Longitude", "Error"]] = geocoded_results
    else:
        raise ValueError("Geocoding results do not match expected dimensions.")

    # Update only the rows that were processed
    if os.path.exists(output_file):
        for index, row in rows_to_process.iterrows():
            if index in existing_df.index:
                existing_row = existing_df.loc[index]
                # Check if the row has been updated
                if (
                    row["Latitude"] != existing_row["Latitude"]
                    or row["Longitude"] != existing_row["Longitude"]
                    or row["Error"] != existing_row["Error"]
                ):
                    print(f"Updated record at index {index}:")
                    print(row)
                # Clear the error if latitude and longitude are valid
                if pd.notna(row["Latitude"]) and pd.notna(row["Longitude"]):
                    rows_to_process.at[index, "Error"] = None

        # Update the existing DataFrame with the processed rows
        for index, row in rows_to_process.iterrows():
            existing_df.loc[index, ["Latitude", "Longitude", "Error"]] = row[
                ["Latitude", "Longitude", "Error"]
            ]

        final_df = existing_df
    else:
        # Clear the error for rows with valid latitude and longitude
        rows_to_process.loc[
            rows_to_process["Latitude"].notna() & rows_to_process["Longitude"].notna(),
            "Error",
        ] = None
        final_df = pd.concat([df, rows_to_process]).drop_duplicates(
            subset=columns_to_geocode.keys(), keep="last"
        )

    # Save the updated DataFrame
    final_df.to_csv(output_file, index=False)

    print(f"Geocoding complete. Updated file saved to {output_file}")


# Process chapters.csv
chapters_file = "data/location/cities.csv"
chapters_output = "data/location/geocoded_cities.csv"
chapters_df = load_data(chapters_file, dtype={"Zip": str})
process_geocoding(
    chapters_df,
    chapters_output,
    columns_to_geocode={
        "City": "City",
        "State": "State",
        "Zip": "Zip",
    },  # No "Address" key here
)

# Process members.csv
members_file = "data/location/poi.csv"
members_output = "data/location/geocoded_poi.csv"
members_df = load_data(members_file, dtype={"Zip": str})
process_geocoding(
    members_df,
    members_output,
    columns_to_geocode={
        "Address": "Address",
        "City": "City",
        "State": "State",
        "Zip": "Zip",
    },
)
