import streamlit as st
import json
from shapely.geometry import shape, Point, Polygon, MultiPolygon
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# --- Load GeoJSON with cache ---
@st.cache_data
def load_geojson():
    with open('data/ElSpot_omraade.geojson', "r", encoding="utf-8") as f:
        return json.load(f)

geojson_data = load_geojson()

st.title("Norway Price Areas Map (NO1-NO5)")

# --- Initialize session state ---
if "clicked_point" not in st.session_state:
    st.session_state.clicked_point = None
if "selected_area" not in st.session_state:
    st.session_state.selected_area = None

# --- Function to find which area contains a point ---
def find_price_area(lat, lon):
    point = Point(lon, lat)
    for feature in geojson_data["features"]:
        geom = feature["geometry"]
        if geom["type"] == "Polygon":
            polygon = shape(geom)
            if polygon.contains(point):
                return feature["properties"].get("ElSpotOmr", "Unknown")
        elif geom["type"] == "MultiPolygon":
            multipolygon = shape(geom)
            if multipolygon.contains(point):
                return feature["properties"].get("ElSpotOmr", "Unknown")
    return None

# --- Create Plotly figure ---
fig = go.Figure()

# Draw all polygons
for feature in geojson_data["features"]:
    area_name = feature["properties"].get("ElSpotOmr", "Unknown")
    geom = feature["geometry"]

    # Handle both Polygon and MultiPolygon
    polygons = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]

    for poly in polygons:
        for coords in poly:
            lons, lats = zip(*coords)
            # Highlight selected area
            line_color = "red" if st.session_state.selected_area == area_name else "blue"
            fill_color = "yellow" if st.session_state.selected_area == area_name else "rgba(0,0,255,0.1)"
            fig.add_trace(go.Scattermapbox(
                lon=lons,
                lat=lats,
                mode="lines",
                fill="toself",
                fillcolor=fill_color,
                line=dict(color=line_color, width=2),
                name=area_name,
                hoverinfo="text",
                text=f"Price area: {area_name}"
            ))

# Add clicked point marker
if st.session_state.clicked_point:
    lat, lon = st.session_state.clicked_point
    fig.add_trace(go.Scattermapbox(
        lat=[lat],
        lon=[lon],
        mode="markers",
        marker=dict(size=12, color="red"),
        name="Clicked Point"
    ))

# Set map layout
fig.update_layout(
    mapbox=dict(
        style="carto-positron",
        center=dict(lat=63, lon=10.5),
        zoom=5.5
    ),
    margin={"r":0,"t":0,"l":0,"b":0},
    showlegend=False
)

# --- Display map and capture clicks ---
clicked_points = plotly_events(
    fig,
    click_event=True,
    hover_event=False,
    select_event=False,
    override_height=600,
    override_width="100%"
)

# --- Update session state if clicked ---
if clicked_points:
    lat = clicked_points[0]["lat"]
    lon = clicked_points[0]["lon"]
    st.session_state.clicked_point = (lat, lon)
    st.session_state.selected_area = find_price_area(lat, lon)
    st.experimental_rerun()  # refresh to show marker & highlighted polygon

# --- Display info ---
if st.session_state.clicked_point:
    st.write("Clicked coordinates:", st.session_state.clicked_point)
    if st.session_state.selected_area:
        st.write("Price area selected:", st.session_state.selected_area)
    else:
        st.write("No Price area at this point.")
