/** This template calculates the distance and area of drawn shapes using the Haversine formula
 *  and displays the results in tooltips. It also handles the conversion of units to miles and acres.
 *  This is done Because L.GeometryUtil.geodesicLength() and .length are not available in Foliums Leaflet implementation
 *  Conversion factors: multiply by these to convert to desired units
 *  meters to miles = 1 / 1609.34 ≈ 0.000621371
 *  m² (sq meters) to acres = 1 / 4046.8564224 ≈ 0.000247105
 *  Reference: https://en.wikipedia.org/wiki/Haversine_formula
 **/
// Haversine formula
function haversineDistance(latlngs) {
  const R = 6371000; // Radius of the Earth in meters
  let totalDistance = 0;

  for (let i = 0; i < latlngs.length - 1; i++) {
    const [lat1, lon1] = [latlngs[i].lat, latlngs[i].lng];
    const [lat2, lon2] = [latlngs[i + 1].lat, latlngs[i + 1].lng];

    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;

    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    totalDistance += R * c;
  }

  return totalDistance; // Distance in meters
}

map.on(L.Draw.Event.CREATED, function (e) {
  const layer = e.layer,
    type = e.layerType;

  if (type === 'polyline') {
    // Calculate and display length in miles using haversineDistance function
    const latlngs = layer.getLatLngs();
    const length = haversineDistance(latlngs);
    const lengthInMiles = (length * 0.000621371).toFixed(2); // Convert meters to miles
    layer
      .bindTooltip(`Length: ${lengthInMiles} miles`, {
        permanent: false,
        direction: 'top',
        offset: [0, -10],
      })
      .openTooltip();
  } else if (type === 'polygon' || type === 'rectangle') {
    // Calculate and display area in acres
    const area = L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
    const areaInAcres = (area * 0.000247105).toFixed(2); // Convert m² to acres
    layer.bindTooltip(`Area: ${areaInAcres} acres`, {
      permanent: false,
      direction: 'top',
      offset: [0, -10],
    });
  } else if (type === 'circle') {
    // Calculate and display radius in miles
    const radiusInMiles = (layer.getRadius() * 0.000621371).toFixed(2);
    layer.bindTooltip(`Radius: ${radiusInMiles} miles`, {
      permanent: false,
      direction: 'top',
      offset: [0, -10],
    });
  } else if (type === 'marker') {
    // Display coordinates for markers
    const lat = layer.getLatLng().lat.toFixed(6);
    const lng = layer.getLatLng().lng.toFixed(6);
    layer.bindTooltip(`Coordinates: (${lat}, ${lng})`, {
      permanent: false,
      direction: 'top',
      offset: [0, 0],
    });
  }

  // Add the layer to the drawing layer
  map.addLayer(layer);
});

/** This template adds a button to the map that allows users to generate isochrones by clicking on the map.
 * It also handles the display of tooltips with latitude and longitude coordinates.
 * The button is styled and positioned on the map, and it includes functionality to disable marker popups
 * and tooltips while the isochrone mode is active.
 * The script also includes error handling for the isochrone generation process.
 * The button is removed when the Escape key is pressed, and the tooltip is removed after the map is clicked.
 **/

// Initialize Layer Control to dynamically add layers
let isIsochroneMode = false; // Flag to track isochrone mode
let layerControl = null; // Do not add layer control initially

// Add a custom button to the map
const button = L.control({ position: 'topright' });
button.onAdd = function (map) {
  const div = L.DomUtil.create(
    'div',
    'leaflet-bar leaflet-control leaflet-control-custom'
  );
  div.innerHTML =
    '<button id="isochrone-btn" style="background-color: white; border: none; padding: 5px; cursor: pointer;">Add Isochrone</button>';
  div.style.backgroundColor = 'white';
  div.style.width = 'auto';
  div.style.height = 'auto';
  return div;
};
button.addTo(map);

// Handle button click
document
  .getElementById('isochrone-btn')
  .addEventListener('click', function (event) {
    event.stopPropagation(); // Prevent the button click from propagating to the map
    console.log('Add Isochrone button clicked');

    isIsochroneMode = true; // Enable isochrone mode

    // Disable marker popups and tooltips
    map.eachLayer(function (layer) {
      if (layer instanceof L.Marker) {
        layer.off('click'); // Disable marker click events
      }
    });

    let tooltip = L.tooltip({
      permanent: false,
      direction: 'right',
      offset: [12, 0],
    });

    // Add a mousemove listener to the map
    function onMouseMove(e) {
      const lat = e.latlng.lat.toFixed(6);
      const lng = e.latlng.lng.toFixed(6);
      tooltip
        .setLatLng(e.latlng)
        .setContent(`Lat: ${lat}, Lng: ${lng}<br>Click Here`)
        .addTo(map);
    }

    map.on('mousemove', onMouseMove);

    // Enable map click listener
    function onMapClick(e) {
      const lat = e.latlng.lat;
      const lng = e.latlng.lng;

      console.log(`Map clicked at latitude: ${lat}, longitude: ${lng}`);

      // Create a new feature group for the circle
      const isochroneLayer = L.featureGroup().addTo(map);
      const inputName = prompt(
        'Enter a name for the isochrone layer:',
        'Isochrone'
      );
      const layerName = `${inputName} at (${lat.toFixed(6)}, ${lng.toFixed(
        6
      )})`;

      // Add layer control to the map if it doesn't exist
      if (!layerControl) {
        layerControl = L.control
          .layers(null, {}, { collapsed: false })
          .addTo(map);
        const layerControlName = prompt(
          'Enter a name for the layer control:',
          'User Generated Layers'
        );
        const title = document.createElement('div');
        title.style =
          'font-weight: bold; font-size: 14px; margin-bottom: 5px; border-bottom: 1px solid #ccc;';
        title.innerHTML = layerControlName;
        layerControl
          .getContainer()
          .insertBefore(title, layerControl.getContainer().firstChild);
      }

      // Add the new layer to the layer control
      layerControl.addOverlay(isochroneLayer, layerName);

      // Call your backend API to generate the isochrone
      fetch(`/generate_isochrone?lat=${lat}&lng=${lng}&time=1800`)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
          }
          return response.json();
        })
        .then((data) => {
          if (!data || !data.features) {
            throw new Error('Invalid GeoJSON object.');
          }
          const isochronePolygon = L.geoJSON(data, {
            style: {
              color: 'blue',
              weight: 2,
              fillOpacity: 0.4,
            },
          });

          isochronePolygon.addTo(isochroneLayer);
          // isochroneLayer.addTo(map);
          isochronePolygon.bindTooltip(`Isochrone for ${layerName}`, {
            permanent: false,
            direction: 'top',
            offset: [0, -10],
          });
        })
        .catch((error) => {
          console.error('Error generating isochrone:', error);
          alert(`Failed to generate isochrone: ${error.message}`);
        });

      // Remove the tooltip and mousemove listener after the map is clicked
      cleanup();
    }

    map.once('click', onMapClick);

    // End the event when the Escape key is pressed
    function onKeyDown(e) {
      if (e.key === 'Escape') {
        console.log('Escape key pressed, ending isochrone event');
        cleanup();
      }
    }

    document.addEventListener('keydown', onKeyDown);

    // Cleanup function to remove all listeners and the tooltip
    function cleanup() {
      isIsochroneMode = false; // Disable isochrone mode

      // Re-enable marker popups and tooltips
      map.eachLayer(function (layer) {
        if (layer instanceof L.Marker) {
          layer.on('click', function (e) {
            layer.openPopup(); // Re-enable marker click events
          });
        }
      });

      map.off('mousemove', onMouseMove);
      map.off('click', onMapClick);
      map.removeLayer(tooltip);
      document.removeEventListener('keydown', onKeyDown);
    }
  });
