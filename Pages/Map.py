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
    point = Point(lon, lat)  # GeoJSON uses (lon, lat)
    for feature in geojson_data["features"]:
        polygon = shape(feature["geometry"])
        if polygon.contains(point):
            return feature["properties"].get("ElSpotOmr", "Unknown")
    return None

# --- Build the map figure ---
fig = go.Figure()

# Draw polygons
for feature in geojson_data["features"]:
    area_name = feature["properties"].get("ElSpotOmr", "Unknown")
    geom = feature["geometry"]
    coords_list = geom["coordinates"] if geom["type"] == "Polygon" else [c for c in geom["coordinates"]]
    
    for coords in coords_list:
        lons, lats = zip(*coords[0] if geom["type"] == "MultiPolygon" else coords)
        is_selected = (st.session_state.selected_area == area_name)
        fig.add_trace(go.Scattermap(
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

# Add marker for clicked point
if st.session_state.clicked_point:
    lat, lon = st.session_state.clicked_point
    fig.add_trace(go.Scattermap(
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
clicked = plotly_events(
    fig,
    click_event=True,
    hover_event=False,
    select_event=False,
    override_height=600,
    override_width="100%"
)

# Update session state if clicked
if clicked:
    click_data = clicked[0]
    # Scattermap returns lat/lon in 'y' and 'x' for plotly_events
    lat = click_data.get("y")
    lon = click_data.get("x")
    if lat is not None and lon is not None:
        st.session_state.clicked_point = (lat, lon)
        st.session_state.selected_area = find_price_area(lat, lon)
        st.experimental_rerun()  # refresh map with marker & highlight

# --- Display info ---
if st.session_state.clicked_point:
    st.write("Clicked coordinates:", st.session_state.clicked_point)
    if st.session_state.selected_area:
        st.write("Price area selected:", st.session_state.selected_area)
    else:
        st.write("No Price area at this point.")
