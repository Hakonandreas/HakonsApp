import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from functions.elhub_utils import load_elhub_data, load_elhub_consumption
from functions.weather_utils import download_era5_data

# Path to uploaded screenshot (developer instruction: supply local path)
screenshot_path = "/mnt/data/Skjermbilde 2025-11-23 kl. 11.04.06.png"

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
def load_all_data(year=2023, lat=60.0, lon=10.0):
    # Load meteo (ERA5)
    weather = download_era5_data(latitude=lat, longitude=lon, year=year)

    # Load Elhub production + consumption
    prod_df = load_elhub_data()
    cons_df = load_elhub_consumption()

    # --- Force timezone-awareness ---
    weather["time"] = pd.to_datetime(weather["time"], utc=True)
    prod_df["starttime"] = pd.to_datetime(prod_df["starttime"], utc=True)
    cons_df["starttime"] = pd.to_datetime(cons_df["starttime"], utc=True)

    # --- Drop only _id if present (per your request) ---
    if "_id" in prod_df.columns:
        prod_df = prod_df.drop(columns=["_id"])
    if "_id" in cons_df.columns:
        cons_df = cons_df.drop(columns=["_id"])

    # --- Convert to numeric where possible and set index for resampling ---
    prod_df_numeric = prod_df.set_index("starttime").apply(pd.to_numeric, errors="coerce")
    cons_df_numeric = cons_df.set_index("starttime").apply(pd.to_numeric, errors="coerce")

    # --- Resample hourly (mean) and interpolate small gaps ---
    prod_hourly = prod_df_numeric.resample("h").mean().interpolate()
    cons_hourly = cons_df_numeric.resample("h").mean().interpolate()

    # --- Save lists of clean variable names (displayed to user) ---
    prod_vars = prod_hourly.columns.tolist()
    cons_vars = cons_hourly.columns.tolist()

    # --- To avoid column-overlap errors, add suffixes to the Elhub hourly dataframes for merging ---
    prod_hourly_suff = prod_hourly.add_suffix("_prod")
    cons_hourly_suff = cons_hourly.add_suffix("_cons")

    # --- Merge: weather + production + consumption (inner join on time) ---
    df = (
        weather.set_index("time")
        .join(prod_hourly_suff, how="inner")
        .join(cons_hourly_suff, how="inner")
    )

    # Return merged df plus original variable lists (unsuffixed names for display)
    return df, prod_vars, cons_vars, weather

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("Meteorology & Energy — Sliding Window Correlation (Streamlit + Plotly)")

# show uploaded screenshot (optional)
try:
    st.image(screenshot_path, caption="Screenshot (uploaded)", use_column_width=True)
except Exception:
    # ignore if file absent
    pass

# Load data (cached)
df, prod_vars, cons_vars, weather_df = load_all_data()

# Meteorological variables to offer (explicit list to avoid offering internal metadata)
weather_vars = [
    "temperature_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_gusts_10m",
    "wind_direction_10m"
]

# -----------------------------
# Top UI: data type and meteo selector side-by-side
# -----------------------------
left, right = st.columns([1, 2])

with left:
    st.write("### Data Type")
    data_type = st.radio("", ["Production", "Consumption"], horizontal=True)

with right:
    st.write("### Meteorology Variable")
    meta_var = st.selectbox("Select meteorological variable:", weather_vars)

# -----------------------------
# Energy variable selector (side-by-side with controls)
# -----------------------------
col_energy, col_controls = st.columns([2, 1])

with col_energy:
    st.write("### Energy Variable")

    if data_type == "Production":
        if len(prod_vars) == 0:
            st.error("No production variables available in production dataset.")
            st.stop()
        selected_energy_display = st.selectbox("Select production variable:", prod_vars)
        energy_internal_col = f"{selected_energy_display}_prod"
    else:
        if len(cons_vars) == 0:
            st.error("No consumption variables available in consumption dataset.")
            st.stop()
        selected_energy_display = st.selectbox("Select consumption variable:", cons_vars)
        energy_internal_col = f"{selected_energy_display}_cons"

with col_controls:
    st.write("### SWC parameters")
    window = st.slider("Window length (hours)", 24, 500, 120)
    lag = st.slider("Lag (hours)", -72, 72, 0)

# -----------------------------
# Basic checks
# -----------------------------
if meta_var not in df.columns:
    st.error(f"Selected meteorological variable '{meta_var}' not present in merged data.")
    st.stop()

if energy_internal_col not in df.columns:
    st.error(f"Selected energy variable '{selected_energy_display}' not present after merge (internal: {energy_internal_col}).")
    st.stop()

# -----------------------------
# Compute SWC
# -----------------------------
swc = sliding_window_corr(df[meta_var], df[energy_internal_col], window=window, lag=lag)

# -----------------------------
# Plot with Plotly: meteorology (left axis), energy (right axis), SWC (separate line)
# -----------------------------
fig = go.Figure()

# Meteorology series
fig.add_trace(go.Scatter(
    x=df.index,
    y=df[meta_var],
    name=f"Meteo: {meta_var}",
    line=dict(width=1)
))

# Energy series (right axis)
fig.add_trace(go.Scatter(
    x=df.index,
    y=df[energy_internal_col],
    name=f"Energy: {selected_energy_display}",
    yaxis="y2",
    line=dict(width=1)
))

# SWC series (standalone)
fig.add_trace(go.Scatter(
    x=df.index,
    y=swc,
    name="Sliding Window Corr",
    line=dict(width=2),
    marker=dict(opacity=0.6)
))

fig.update_layout(
    title=f"Sliding Window Correlation — {meta_var} vs {selected_energy_display} (window={window}, lag={lag})",
    height=700,
    hovermode="x unified",
    xaxis=dict(title="Time"),
    yaxis=dict(title=meta_var),
    yaxis2=dict(title=selected_energy_display, overlaying="y", side="right")
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Summary Stats & quick checks (for your notebook logging)
# -----------------------------
st.subheader("Correlation Summary")
st.write(f"**Mean SWC:** {float(swc.mean()):.3f}")
st.write(f"**Max SWC:** {float(swc.max()):.3f}")
st.write(f"**Min SWC:** {float(swc.min()):.3f}")

st.write("---")
st.markdown("### Data inspection")
st.write("Merged dataframe preview (first rows):")
st.dataframe(df.head())

# Small helper: expose the internal col names so you can copy them to notebook if needed
st.write("Internal column used for energy (suffixed):", energy_internal_col)
