import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from functions.elhub_utils import load_elhub_data, load_elhub_consumption
from functions.weather_utils import download_era5_data


# -----------------------------
# Sliding Window Correlation
# -----------------------------
def sliding_window_corr(series_x, series_y, window, lag):
    shifted_y = series_y.shift(lag)
    return series_x.rolling(window=window, center=True).corr(shifted_y)


# -----------------------------
# Load and merge using existing functions
# -----------------------------
@st.cache_data
def load_all_data():

    # Load meteo (ERA5)
    weather = download_era5_data(
        latitude=60.0,
        longitude=10.0,
        year=2023
    )

    # Load Elhub production + consumption
    prod_df = load_elhub_data()              # PRODUCTION
    cons_df = load_elhub_consumption()       # CONSUMPTION

    # Fix timestamps
    weather["time"] = pd.to_datetime(weather["time"], utc=True)
    prod_df["starttime"] = pd.to_datetime(prod_df["starttime"], utc=True)
    cons_df["starttime"] = pd.to_datetime(cons_df["starttime"], utc=True)

    # Convert all values to numeric
    prod_df_numeric = prod_df.set_index("starttime").apply(pd.to_numeric, errors="coerce")
    cons_df_numeric = cons_df.set_index("starttime").apply(pd.to_numeric, errors="coerce")

    # Resample hourly
    prod_hourly = prod_df_numeric.resample("H").mean().interpolate()
    cons_hourly = cons_df_numeric.resample("H").mean().interpolate()

    # Merge all together
    df = (
        weather.set_index("time")
        .join(prod_hourly, how="inner")
        .join(cons_hourly, how="inner")
    )

    return df, prod_hourly, cons_hourly


# -----------------------------
# Streamlit UI
# -----------------------------
st.title("Meteorology & Energy: Sliding Window Correlation Explorer")

df, prod_hourly, cons_hourly = load_all_data()

# Weather variables (keep manual list)
weather_vars = [
    "temperature_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_gusts_10m",
    "wind_direction_10m"
]

# Extract real production/consumption variables
prod_vars = [c for c in prod_hourly.columns if not c.endswith("_id")]
cons_vars = [c for c in cons_hourly.columns if not c.endswith("_id")]


# -----------------------------
# UI Selectors — side by side
# -----------------------------
top1, top2 = st.columns(2)

with top1:
    st.write("### Data Type")
    data_type = st.radio(
        "",
        ["Production", "Consumption"],
        horizontal=True
    )

with top2:
    st.write("### Meteorology Variable")
    meta_var = st.selectbox("Select meteo variable:", weather_vars)


# Energy variable selector
col1, col2 = st.columns(2)

with col1:
    st.write("### Energy Variable")
    if data_type == "Production":
        energy_var = st.selectbox("Select production variable:", prod_vars)
    else:
        energy_var = st.selectbox("Select consumption variable:", cons_vars)


# -----------------------------
# Controls
# -----------------------------
window = st.slider("Window length (hours)", 24, 500, 120)
lag = st.slider("Lag (hours)", -72, 72, 0)


# -----------------------------
# Compute SWC
# -----------------------------
swc = sliding_window_corr(
    df[meta_var],
    df[energy_var],
    window=window,
    lag=lag
)


# -----------------------------
# Plot
# -----------------------------
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df.index,
    y=df[meta_var],
    name=f"Weather: {meta_var}",
    line=dict(width=1)
))

fig.add_trace(go.Scatter(
    x=df.index,
    y=df[energy_var],
    name=f"Energy: {energy_var}",
    yaxis="y2",
    line=dict(width=1)
))

fig.add_trace(go.Scatter(
    x=df.index,
    y=swc,
    name="Sliding Window Corr",
    line=dict(width=2, color="red")
))

fig.update_layout(
    title=f"Sliding Window Correlation (window={window}, lag={lag})",
    height=650,
    hovermode="x unified",
    xaxis=dict(title="Time"),
    yaxis=dict(title=meta_var),
    yaxis2=dict(
        title=energy_var,
        overlaying="y",
        side="right"
    )
)

st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# Summary
# -----------------------------
st.subheader("Correlation Summary")
st.write(f"**Mean SWC:** {swc.mean():.3f}")
st.write(f"**Max SWC:** {swc.max():.3f}")
st.write(f"**Min SWC:** {swc.min():.3f}")
