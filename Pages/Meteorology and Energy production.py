import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from functions.elhub_utils import load_elhub_data, load_elhub_consumption
from functions.weather_utils import download_era5_data

# -----------------------------
# Sliding Window Correlation
# -----------------------------
def sliding_window_corr(series_x, series_y, window, lag):
    shifted_y = series_y.shift(lag)
    return series_x.rolling(window=window, center=True).corr(shifted_y)

def lagged_corr(series_x, series_y, lag):
    """Direct lagged correlation like in lecture notes."""
    if lag > 0:
        return np.corrcoef(series_x[lag:], series_y[:-lag])[0, 1]
    elif lag < 0:
        return np.corrcoef(series_x[:lag], series_y[-lag:])[0, 1]
    else:
        return np.corrcoef(series_x, series_y)[0, 1]

# -----------------------------
# Load and merge
# -----------------------------
@st.cache_data
def load_all_data(year=2023, lat=60.0, lon=10.0):
    weather = download_era5_data(latitude=lat, longitude=lon, year=year)
    prod_df = load_elhub_data()
    cons_df = load_elhub_consumption()

    # timezone
    weather["time"] = pd.to_datetime(weather["time"], utc=True)
    prod_df["starttime"] = pd.to_datetime(prod_df["starttime"], utc=True)
    cons_df["starttime"] = pd.to_datetime(cons_df["starttime"], utc=True)

    # drop _id
    for df in [prod_df, cons_df]:
        if "_id" in df.columns:
            df.drop(columns=["_id"], inplace=True)

    # numeric + resample
    prod_hourly = prod_df.set_index("starttime").apply(pd.to_numeric, errors="coerce").resample("h").mean().interpolate()
    cons_hourly = cons_df.set_index("starttime").apply(pd.to_numeric, errors="coerce").resample("h").mean().interpolate()

    prod_vars = prod_hourly.columns.tolist()
    cons_vars = cons_hourly.columns.tolist()

    prod_hourly_suff = prod_hourly.add_suffix("_prod")
    cons_hourly_suff = cons_hourly.add_suffix("_cons")

    df = (
        weather.set_index("time")
        .join(prod_hourly_suff, how="inner")
        .join(cons_hourly_suff, how="inner")
    )
    return df, prod_vars, cons_vars, weather

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("Meteorology & Energy — Sliding Window Correlation")

df, prod_vars, cons_vars, weather_df = load_all_data()

weather_vars = ["temperature_2m","precipitation","wind_speed_10m","wind_gusts_10m","wind_direction_10m"]

# 1. Data type
data_type = st.radio("Select dataset:", ["Production", "Consumption"], horizontal=True)

# 2. Meteo + Energy
col_meteo, col_energy = st.columns([1,2])
with col_meteo:
    meta_var = st.selectbox("Meteorological variable:", weather_vars)
with col_energy:
    if data_type == "Production":
        selected_energy_display = st.selectbox("Production variable:", prod_vars)
        energy_internal_col = f"{selected_energy_display}_prod"
    else:
        selected_energy_display = st.selectbox("Consumption variable:", cons_vars)
        energy_internal_col = f"{selected_energy_display}_cons"

# 3. SWC parameters
window = st.slider("Window length (hours)", 24, 500, 120)
lag = st.slider("Lag (hours)", -72, 72, 0)

# -----------------------------
# Compute correlations
# -----------------------------
swc = sliding_window_corr(df[meta_var], df[energy_internal_col], window=window, lag=lag)
lag_corr_value = lagged_corr(df[meta_var].dropna().values, df[energy_internal_col].dropna().values, lag)

# -----------------------------
# Plot
# -----------------------------
fig = go.Figure()

fig.add_trace(go.Scatter(x=df.index, y=df[meta_var], name=f"Meteo: {meta_var}", line=dict(width=1)))
fig.add_trace(go.Scatter(x=df.index, y=df[energy_internal_col], name=f"Energy: {selected_energy_display}", yaxis="y2", line=dict(width=1)))
fig.add_trace(go.Scatter(x=df.index, y=swc, name="SWC", line=dict(width=2)))

fig.update_layout(
    title=f"SWC — {meta_var} vs {selected_energy_display} (window={window}, lag={lag})",
    height=700,
    hovermode="x unified",
    xaxis=dict(title="Time"),
    yaxis=dict(title=meta_var),
    yaxis2=dict(title=selected_energy_display, overlaying="y", side="right")
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Summary
# -----------------------------
with st.expander("Correlation Summary & Data Preview"):
    st.write(f"**Direct lagged correlation (lag={lag}):** {lag_corr_value:.3f}")
    st.write(f"**Mean SWC:** {float(swc.mean()):.3f}")
    st.write(f"**Max SWC:** {float(swc.max()):.3f}")
    st.write(f"**Min SWC:** {float(swc.min()):.3f}")
    st.dataframe(df.head())
    st.write("Internal energy column:", energy_internal_col)
