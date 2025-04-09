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
