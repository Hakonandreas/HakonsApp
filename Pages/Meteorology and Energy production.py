import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ---------------------------------------------------------
# Utility: compute sliding window correlation with lag
# ---------------------------------------------------------
def sliding_window_corr(series_x, series_y, window, lag):
    """
    Compute sliding-window correlation between two aligned series.
    Positive lag means Y is shifted forward (X leads Y).
    """
    y_shifted = series_y.shift(lag)
    return series_x.rolling(window, center=True).corr(y_shifted)

# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
@st.cache_data
def load_data():
    weather = download_era5_data(latitude=60.0, longitude=10.0, year=2023)
    prod = load_elhub_data()
    cons = load_elhub_consumption()

    # Resample to hourly means / sums (depends on your data)
    prod_hourly = prod.resample("H", on="starttime").mean().interpolate()
    cons_hourly = cons.resample("H", on="starttime").mean().interpolate()

    # Merge everything on datetime index
    df = weather.set_index("time").join(prod_hourly, how="inner", rsuffix="_prod").join(cons_hourly, how="inner", rsuffix="_cons")

    return df

df = load_data()

st.title("Sliding Window Correlation: Weather vs. Energy Production/Consumption")
st.markdown("""
Use this dashboard to explore how weather variables correlate with energy production and consumption over time.
""")

# ---------------------------------------------------------
# Selectors
# ---------------------------------------------------------
weather_cols = ["temperature_2m", "precipitation", "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m"]
energy_cols = [c for c in df.columns if ("production" in c.lower() or "consumption" in c.lower())]

meta_var = st.selectbox("Meteorological variable:", weather_cols)
energy_var = st.selectbox("Energy variable:", energy_cols)

window = st.slider("Window length", min_value=24, max_value=500, value=100, step=1)
lag = st.slider("Lag (hours)", min_value=-72, max_value=72, value=0, step=1)

# ---------------------------------------------------------
# Compute SWC
# ---------------------------------------------------------
swc = sliding_window_corr(df[meta_var], df[energy_var], window=window, lag=lag)

# ---------------------------------------------------------
# Plotly visualization
# ---------------------------------------------------------
fig = go.Figure()

# Top plot: meteorology
fig.add_trace(go.Scatter(
    x=df.index, y=df[meta_var], name=meta_var,
    line=dict(width=1)
))

# Energy plot (secondary axis)
fig.add_trace(go.Scatter(
    x=df.index, y=df[energy_var], name=energy_var,
    line=dict(width=1), yaxis="y2"
))

# SWC plot
fig.add_trace(go.Scatter(
    x=df.index, y=swc, name="SWC",
    line=dict(width=2, color="red")
))

# Layout
fig.update_layout(
    height=600,
    title=f"Sliding Window Correlation (window={window}, lag={lag})",
    xaxis=dict(title="Time"),
    yaxis=dict(title=meta_var),
    yaxis2=dict(title=energy_var, overlaying="y", side="right"),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# Summary
st.subheader("Correlation summary")
st.write(f"Average SWC: **{swc.mean():.3f}**")
st.write(f"Maximum SWC: **{swc.max():.3f}**")
st.write(f"Minimum SWC: **{swc.min():.3f}**")
