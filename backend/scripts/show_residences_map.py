import folium
import json
import os

# Define the file path for the GeoJSON
geojson_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'residences.geojson')

# Create the base map
m = folium.Map(location=[32.9715285, -89.7348497], zoom_start=6)

# Add GeoJSON to map
with open(geojson_file) as f:
    geojson_data = json.load(f)
    folium.GeoJson(geojson_data, name='Residence Events').add_to(m)

# Save the map as HTML
output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'residences_map.html')
m.save(output_file)

print(f"🌍 Map saved to {output_file}")
