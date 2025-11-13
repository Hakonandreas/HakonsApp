import streamlit as st
import json
from shapely.geometry import shape, Point
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# --- Load GeoJSON ---
@st.cache_data
def load_geojson():
    with open('data/ElSpot_omraade.geojson', "r", encoding="utf-8") as f:
        return json.load(f)

geojson_data = load_geojson()

st.title("Norway Price Areas Map (NO1-NO5)")

# --- Session state ---
if "clicked_point" not in st.session_state:
    st.session_state.clicked_point = None
if "selected_area" not in st.session_state:
    st.session_state.selected_area = None

# --- Function to find which Price Area contains a point ---
def find_price_area(lat, lon):
    point = Point(lon, lat)
    for feature in geojson_data["features"]:
        polygon = shape(feature["geometry"])
        if polygon.contains(point):
            return feature["properties"].get("ElSpotOmr", "Unknown")
    return None

# --- Build the map figure ---
fig = go.Figure()

for feature in geojson_data["features"]:
    area_name = feature["properties"].get("ElSpotOmr", "Unknown")
    geom = feature["geometry"]

    # Handle Polygon vs MultiPolygon
    if geom["type"] == "Polygon":
        coords_list = geom["coordinates"][0]  # first linear ring
        polygons = [coords_list]
    elif geom["type"] == "MultiPolygon":
        polygons = [poly[0] for poly in geom["coordinates"]]  # first ring of each polygon
    else:
        continue

    for coords in polygons:
        lons, lats = zip(*coords)
        is_selected = (st.session_state.selected_area == area_name)
        fig.add_trace(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode="lines",
            fill="toself",
            fillcolor="yellow" if is_selected else "rgba(0,0,255,0.1)",
            line=dict(color="red" if is_selected else "blue", width=2),
            hoverinfo="text",
