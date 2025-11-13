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
            text=f"Price area: {area_name}",
            name=area_name,
            showlegend=False
        ))

# Add clicked point marker
if st.session_state.clicked_point:
    lat, lon = st.session_state.clicked_point
    fig.add_trace(go.Scattermapbox(
        lon=[lon],
        lat=[lat],
        mode="markers",
        marker=dict(size=12, color="red"),
        name="Clicked Point",
        showlegend=False
    ))

# Map layout
fig.update_layout(
    mapbox_style="open-street-map",
    mapbox=dict(center=dict(lat=63, lon=10.5), zoom=5.5),
    margin={"r":0,"t":0,"l":0,"b":0}
)

# --- Capture clicks ---
clicked_points = plotly_events(
    fig,
    click_event=True,
    hover_event=False,
    select_event=False,
    override_height=600,
    override_width="100%"
)

# Update session state if clicked
if clicked_points:
    lat = clicked_points[0].get("lat")
    lon = clicked_points[0].get("lon")
    if lat is not None and lon is not None:
        st.session_state.clicked_point = (lat, lon)
        st.session_state.selected_area = find_price_area(lat, lon)
        st.experimental_rerun()  # refresh map to show marker & highlight

# --- Display info ---
if st.session_state.clicked_point:
    st.write("Clicked coordinates:", st.session_state.clicked_point)
    if st.session_state.selected_area:
        st.write("Price area selected:", st.session_state.selected_area)
    else:
        st.write("No Price area at this point.")
