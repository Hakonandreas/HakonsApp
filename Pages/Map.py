import streamlit as st
import folium
from streamlit_folium import st_folium
import json

# --- Load GeoJSON ---
# Make sure you downloaded ElSpot_omraade.geojson from NVE site
with open("data/ElSpot_omraade.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# --- App title ---
st.title("Norway Price Areas Map (NO1-NO5)")

# --- State to store clicked point and selected area ---
if "clicked_point" not in st.session_state:
    st.session_state.clicked_point = None
if "selected_area" not in st.session_state:
    st.session_state.selected_area = None

# --- Folium Map ---
m = folium.Map(location=[63.0, 10.5], zoom_start=5.5)

# Function to style GeoJSON
def style_function(feature):
    if st.session_state.selected_area == feature["properties"]["name"]:
        return {"fillColor": "#ffff00", "color": "red", "weight": 3, "fillOpacity": 0.2}
    return {"fillColor": "#ffffff", "color": "blue", "weight": 2, "fillOpacity": 0.1}

# Add GeoJSON overlay
folium.GeoJson(
    geojson_data,
    name="Price Areas",
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Price area:"])
).add_to(m)

# Add click handler
def handle_click(lat, lon):
    st.session_state.clicked_point = (lat, lon)
    # Find which area contains the clicked point
    import shapely.geometry
    point = shapely.geometry.Point(lon, lat)
    for feature in geojson_data["features"]:
        polygon = shapely.geometry.shape(feature["geometry"])
        if polygon.contains(point):
            st.session_state.selected_area = feature["properties"]["name"]
            break
    else:
        st.session_state.selected_area = None

# Display map and capture click
map_data = st_folium(m, width=700, height=500, returned_objects=[])

# If user clicked on the map, save coordinates
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    handle_click(lat, lon)

# Display clicked coordinates and selected area
if st.session_state.clicked_point:
    st.write("Clicked coordinates:", st.session_state.clicked_point)
    if st.session_state.selected_area:
        st.write("Price area selected:", st.session_state.selected_area)
    else:
        st.write("No Price area at this point.")
