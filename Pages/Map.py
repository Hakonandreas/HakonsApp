import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from shapely.geometry import shape, Point
from pathlib import Path

# --- Load GeoJSON ---
with open('data/ElSpot_omraade.geojson', "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

st.title("Norway Price Areas Map (NO1-NO5)")

# --- Initialize session state ---
if "clicked_point" not in st.session_state:
    st.session_state.clicked_point = None
if "selected_area" not in st.session_state:
    st.session_state.selected_area = None

# --- Folium Map ---
m = folium.Map(location=[63.0, 10.5], zoom_start=5.5)

# --- Style function using correct property ---
def style_function(feature):
    area_name = feature["properties"].get("ElSpotOmr", "Unknown")
    if st.session_state.selected_area == area_name:
        return {"fillColor": "#ffff00", "color": "red", "weight": 3, "fillOpacity": 0.2}
    return {"fillColor": "#ffffff", "color": "blue", "weight": 2, "fillOpacity": 0.1}

# --- Add GeoJSON overlay ---
folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=["ElSpotOmr"],  # use correct field name
        aliases=["Price area:"],
        localize=True,
        labels=True,
        sticky=False
    )
).add_to(m)

# --- Function to detect clicked area ---
def handle_click(lat, lon):
    st.session_state.clicked_point = (lat, lon)
    point = Point(lon, lat)  # GeoJSON uses (lon, lat)
    for feature in geojson_data["features"]:
        polygon = shape(feature["geometry"])
        if polygon.contains(point):
            st.session_state.selected_area = feature["properties"].get("ElSpotOmr", "Unknown")
            break
    else:
        st.session_state.selected_area = None

# --- Display map and capture clicks ---
map_data = st_folium(m, width=700, height=500, returned_objects=[])
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    handle_click(lat, lon)

# --- Display clicked info ---
if st.session_state.clicked_point:
    st.write("Clicked coordinates:", st.session_state.clicked_point)
    if st.session_state.selected_area:
        st.write("Price area selected:", st.session_state.selected_area)
    else:
        st.write("No Price area at this point.")


