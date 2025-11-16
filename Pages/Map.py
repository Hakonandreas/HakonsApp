import streamlit as st
import folium
from streamlit_folium import st_folium
import json
from shapely.geometry import shape, Point
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import timedelta

from functions.weather_utils import download_era5_data   # <-- IMPORT YOUR FUNCTION HERE

st.title("Norway Price Areas Map (NO1–NO5)")

# ------------------------------------------------------------------------------
# Load GeoJSON
# ------------------------------------------------------------------------------
geojson_path = Path(__file__).parent / "data" / "ElSpot_omraade.geojson"
with open(geojson_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# ------------------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------------------
if "clicked_point" not in st.session_state:
    st.session_state.clicked_point = None

if "selected_area" not in st.session_state:
    st.session_state.selected_area = None

if "area_means" not in st.session_state:
    st.session_state.area_means = None    # stores REAL choropleth values

# ------------------------------------------------------------------------------
# User selections
# ------------------------------------------------------------------------------
variable = st.selectbox(
    "Choose ERA5 variable:",
    ["temperature_2m", "precipitation", "wind_speed_10m", "wind_gusts_10m"]
)

days = st.slider("Time interval (days):", 1, 30, 7)
year = st.selectbox("Year", [2020, 2021, 2022, 2023, 2024])

# ------------------------------------------------------------------------------
# Extract centroid coordinates for each NO area
# ------------------------------------------------------------------------------
def get_area_centroids():
    centroids = {}
    for feature in geojson_data["features"]:
        name = feature["properties"]["ElSpotOmr"]
        polygon = shape(feature["geometry"])
        centroid = polygon.centroid
        centroids[name] = (centroid.y, centroid.x)  # lat, lon
    return centroids

centroids = get_area_centroids()

# ------------------------------------------------------------------------------
# Compute mean ERA5 values per area (cached)
# ------------------------------------------------------------------------------
@st.cache_data(show_spinner=True)
def compute_area_means(variable, days, year, centroids):
    means = {}
    for area, (lat, lon) in centroids.items():

        df = download_era5_data(lat, lon, year)

        end_time = df["time"].max()
        start_time = end_time - timedelta(days=days)

        df_period = df[(df["time"] >= start_time) & (df["time"] <= end_time)]

        means[area] = float(df_period[variable].mean())

    return means

# Compute means when user changes selections
st.session_state.area_means = compute_area_means(
    variable, days, year, centroids
)

means = st.session_state.area_means

# ------------------------------------------------------------------------------
# Color function
# ------------------------------------------------------------------------------
vals = list(means.values())
vmin, vmax = min(vals), max(vals)

def get_color(value):
    norm = (value - vmin) / (vmax - vmin + 1e-9)
    r = int(255 * (1 - norm))
    g = int(255 * norm)
    return f"#{r:02x}{g:02x}00"

# ------------------------------------------------------------------------------
# Build Folium map
# ------------------------------------------------------------------------------
m = folium.Map(location=[63.0, 10.5], zoom_start=5.5)

def style_function(feature):
    area = feature["properties"]["ElSpotOmr"]

    fill = get_color(means[area])

    if st.session_state.selected_area == area:
        return {
            "fillColor": fill,
            "color": "red",
            "weight": 3,
            "fillOpacity": 0.6
        }

    return {
        "fillColor": fill,
        "color": "blue",
        "weight": 1,
        "fillOpacity": 0.4
    }

folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=["ElSpotOmr"], aliases=["Price area:"])
).add_to(m)

if st.session_state.clicked_point:
    folium.Marker(
        st.session_state.clicked_point,
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(m)

# ------------------------------------------------------------------------------
# Click handler
# ------------------------------------------------------------------------------
map_data = st_folium(m, width=800, height=550)

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.session_state.clicked_point = (lat, lon)

    point = Point(lon, lat)
    clicked_area = None

    for feature in geojson_data["features"]:
        polygon = shape(feature["geometry"])
        if polygon.contains(point):
            clicked_area = feature["properties"]["ElSpotOmr"]
            break

    st.session_state.selected_area = clicked_area
    st.rerun()

# ------------------------------------------------------------------------------
# Display information
# ------------------------------------------------------------------------------
st.write("### Choropleth Mean Values:")
st.json(means)

if st.session_state.selected_area:
    st.success(f"Selected area: **{st.session_state.selected_area}**")
