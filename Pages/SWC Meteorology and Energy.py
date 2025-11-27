import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from functions.weather_utils import download_era5_data
from functions.elhub_utils import load_elhub_data, load_elhub_consumption

st.set_page_config(layout="wide")
st.title("Sliding Window Correlation (Daily): Energy vs Weather (NMBU Ås)")

# -------------------------
# Fixed location and year (NMBU Ås)
# -------------------------
LAT, LON = 59.6638, 10.7620
YEAR = 2023

# -------------------------
# Load energy data (from your functions)
# -------------------------
prod_df = load_elhub_data()
cons_df = load_elhub_consumption()

# -------------------------
# Sidebar selectors
# -------------------------
st.sidebar.header("Settings")
variable_weather = st.sidebar.selectbox(
    "Select meteorological variable",
    [
        "temperature_2m",
        "precipitation",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
    ],
)
variable_energy_type = st.sidebar.radio(
    "Select energy type", ["Production", "Consumption"]
)

if variable_energy_type == "Production":
    energy_df = prod_df.copy()
    group_col = "productiongroup"
else:
    energy_df = cons_df.copy()
    group_col = "consumptiongroup"

# defensively handle missing group column
if group_col not in energy_df.columns:
    st.error(f"Expected column '{group_col}' not found in selected energy dataframe.")
    st.stop()

groups = sorted(energy_df[group_col].dropna().unique())
selected_group = st.sidebar.selectbox("Select group", groups)

lag_days = st.sidebar.slider("Lag (days, + means weather leads)", -30, 30, 0)

# -------------------------
# Prepare Elhub series (sum per group, daily)
# -------------------------
energy_series = energy_df[energy_df[group_col] == selected_group].copy()
energy_series["quantitykwh"] = pd.to_numeric(
    energy_series.get("quantitykwh", np.nan), errors="coerce"
)
energy_series = energy_series.dropna(subset=["quantitykwh"])

if "starttime" in energy_series.columns:
    energy_series.index = pd.to_datetime(energy_series["starttime"])
else:
    energy_series.index = pd.to_datetime(energy_series.index)

energy_series = (
    energy_series.groupby(energy_series.index)["quantitykwh"].sum()
    .resample("D")
    .sum()
)

# -------------------------
# Download weather and make daily series (using your download_era5_data)
# -------------------------
weather_df = download_era5_data(latitude=LAT, longitude=LON, year=YEAR)

# Ensure time column exists and is datetime
if "time" in weather_df.columns:
    weather_df["time"] = pd.to_datetime(weather_df["time"])
    weather_df = weather_df.set_index("time")
else:
    weather_df.index = pd.to_datetime(weather_df.index)

weather_series = weather_df[variable_weather]

if variable_weather == "precipitation":
    weather_series = weather_series.resample("D").sum()
else:
    weather_series = weather_series.resample("D").mean()

# Apply lag in days
if lag_days != 0:
    weather_series = weather_series.shift(lag_days)

# -------------------------
# Align data (daily) and DROP TIMEZONE
# -------------------------
df_merged = pd.concat(
    [energy_series.rename("energy"), weather_series.rename("weather")], axis=1
).dropna()

# Make the index tz-naive so it matches slider dates
if df_merged.index.tz is not None:
    df_merged.index = df_merged.index.tz_localize(None)

if df_merged.empty:
    st.warning("No overlapping daily data between energy and weather series.")
    st.stop()

x = df_merged["weather"]
y = df_merged["energy"]

# -------------------------
# Window sliders
# -------------------------
min_win = 5
max_win = min(180, len(df_merged))
default_win = min(60, max_win)
window_days = st.sidebar.slider(
    "Window length (days)", min_win, max_win, default_win
)

date_min = df_merged.index.min().date()
date_max = df_merged.index.max().date()

latest_start = (df_merged.index.max() - pd.Timedelta(days=window_days - 1)).date()
if latest_start < date_min:
    latest_start = date_min

start_date = st.sidebar.slider(
    "Move window across time (start date)",
    min_value=date_min,
    max_value=latest_start,
    value=latest_start,
    format="YYYY-MM-DD",
)

win_start = pd.to_datetime(start_date)  # naive
win_end = win_start + pd.Timedelta(days=window_days - 1)

# -------------------------
# Sliding window correlation
# -------------------------
swc = y.rolling(window_days, center=True).corr(x)
swc_window = swc.loc[win_start:win_end]

corr_value = x.corr(y)

# -------------------------
# Plot energy series (daily)
# -------------------------
fig_energy = go.Figure()
fig_energy.add_trace(
    go.Scatter(
        y=y,
        x=y.index,
        mode="lines",
        name=f"{selected_group}",
        line=dict(color="steelblue"),
    )
)

fig_energy.add_vrect(
    x0=win_start,
    x1=win_end,
    fillcolor="red",
    opacity=0.15,
    line_width=0,
    layer="below",
)

fig_energy.update_layout(
    height=300,
    xaxis_title="Date",
    yaxis_title="Energy (kWh/day)",
    title=f"Daily energy series: {selected_group}",
)
st.plotly_chart(fig_energy, use_container_width=True)

# -------------------------
# Plot weather series (daily)
# -------------------------
fig_weather = go.Figure()
fig_weather.add_trace(
    go.Scatter(
        y=x,
        x=x.index,
        mode="lines",
        name=f"{variable_weather}",
        line=dict(color="steelblue"),
    )
)

fig_weather.add_vrect(
    x0=win_start,
    x1=win_end,
    fillcolor="red",
    opacity=0.15,
    line_width=0,
    layer="below",
)

fig_weather.update_layout(
    height=300,
    xaxis_title="Date",
    yaxis_title=variable_weather,
    title=f"Daily weather series: {variable_weather}",
)
st.plotly_chart(fig_weather, use_container_width=True)

# -------------------------
# Plot sliding window correlation (daily)
# -------------------------
fig_swc = go.Figure()
fig_swc.add_trace(
    go.Scatter(
        y=swc,
        x=swc.index,
        mode="lines",
        name="Sliding Window Corr",
        line=dict(color="steelblue"),
    )
)

fig_swc.add_vrect(
    x0=win_start,
    x1=win_end,
    fillcolor="red",
    opacity=0.10,
    line_width=0,
    layer="below",
)

if not swc_window.dropna().empty:
    fig_swc.add_trace(
        go.Scatter(
            y=swc_window,
            x=swc_window.index,
            mode="lines",
            name="Window SWC",
            line=dict(color="red", width=3),
        )
    )

fig_swc.update_layout(
    height=300,
    xaxis_title="Date",
    yaxis_title="Correlation",
    title=(
        f"Sliding Window Correlation (Daily)\n"
        f"lag={lag_days} days, window={window_days} days, "
        f"overall corr={corr_value:.3f}"
    ),
)
st.plotly_chart(fig_swc, use_container_width=True)

# -------------------------
# Text summary
# -------------------------
st.write(
    f"Overall correlation between **{selected_group}** and "
    f"**{variable_weather}** (daily values): **{corr_value:.3f}**"
)
