import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.fftpack import dct, idct
from sklearn.neighbors import LocalOutlierFactor
import numpy as np
from functions.weather_utils import get_city_from_area, download_era5_data

st.title("Outlier and Anomaly Detection")

# Use the chosen area from session_state
chosen_area = st.session_state.get("chosen_area", None)

city, lat, lon = get_city_from_area(chosen_area)
year = 2021

# Load ERA5 data
st.info(f"Fetching ERA5 data for **{city} ({chosen_area})** — {year}")
df = download_era5_data(lat, lon, year)
df["time"] = pd.to_datetime(df["time"])

# Create tabs
tab_spc, tab_lof = st.tabs(["📈 Outlier / SPC Analysis", "💧 Anomaly / LOF Analysis"])

# OUTLIER / SPC TAB
with tab_spc:
    st.subheader("Seasonally Adjusted Temperature Variation (SPC)")

    # UI controls
    cutoff_frac = st.slider("DCT frequency cut-off fraction", 0.001, 0.05, 0.01, step=0.001)
    n_mad = st.slider("Number of MAD deviations", 1.0, 10.0, 3.0, step=0.5)

    # NaN HANDLING BEFORE DCT (REQUIRED FIX)
    if df["temperature_2m"].isna().any():
        st.warning("NaNs detected — applying linear interpolation before DCT.")
        df["temperature_2m"] = df["temperature_2m"].interpolate()


    # Run analysis
    temp = df["temperature_2m"].values

    # DCT smoothing
    temp_dct = dct(temp, norm='ortho')
    cutoff = int(len(temp) * cutoff_frac)

    temp_dct_low = np.copy(temp_dct)
    temp_dct_low[cutoff:] = 0
    trend = idct(temp_dct_low, norm='ortho')

    satv = temp - trend
    df["SATV"] = satv
    df["Trend"] = trend

    # MAD WITH CORRECT SCALING 1.4826 (REQUIRED FIX)
    median_satv = np.median(satv)
    mad = np.median(np.abs(satv - median_satv))
    mad_scaled = 1.4826 * mad     # Correct robust estimator
    ucl_satv = median_satv + n_mad * mad_scaled
    lcl_satv = median_satv - n_mad * mad_scaled

    df["UCL"] = df["Trend"] + ucl_satv
    df["LCL"] = df["Trend"] + lcl_satv

    # Determine outliers
    df["outlier"] = (df["temperature_2m"] > df["UCL"]) | (df["temperature_2m"] < df["LCL"])
    outliers = df[df["outlier"]]

    # Plotting
    fig = px.line(df, x="time", y="temperature_2m",
                  title=f"Temperature — SPC Outlier Detection ({city}, {year})",
                  labels={"temperature_2m": "Temperature (°C)"})

    fig.add_scatter(x=df["time"], y=df["UCL"], mode="lines",
                    name="UCL", line=dict(color="red", dash="dash"))
    fig.add_scatter(x=df["time"], y=df["LCL"], mode="lines",
                    name="LCL", line=dict(color="red", dash="dash"))
    fig.add_scatter(x=outliers["time"], y=outliers["temperature_2m"],
                    mode="markers", name="Outliers",
                    marker=dict(color="red", size=6, symbol="x"))

    st.plotly_chart(fig, use_container_width=True)

    # IMPROVED SUMMARY: COUNTS + PERCENTAGES (REQUIRED FIX)
    total_n = len(df)
    outlier_n = len(outliers)
    pct_outliers = (outlier_n / total_n) * 100

    st.markdown("### Outlier Summary")
    st.markdown(f"- **Total observations:** {total_n}")
    st.markdown(f"- **Outliers detected:** {outlier_n} ({pct_outliers:.2f}%)")
    # -------------------------------------------------------------------

    st.dataframe(outliers[["time", "temperature_2m", "SATV", "UCL", "LCL"]].head(10))



# ANOMALY / LOF TAB
with tab_lof:
    st.subheader("Precipitation — Local Outlier Factor (LOF)")

    # UI controls
    outlier_frac = st.slider("Proportion of anomalies (only among rainy days)", 0.001, 0.1, 0.01, step=0.005)

    # Prepare data
    precip = df["precipitation"].fillna(0)
    nonzero_mask = precip > 0
    X = np.log1p(precip[nonzero_mask].values.reshape(-1, 1))  # log(1 + x) transform

    
    if np.sum(nonzero_mask) > 20:
        n_neighbors = min(20, len(X) - 1)
        lof = LocalOutlierFactor(n_neighbors=n_neighbors)
        lof.fit(X)
        scores = -lof.negative_outlier_factor_

        # Define threshold using quantile based on slider
        threshold = np.quantile(scores, 1 - outlier_frac)
        anomaly_mask = scores > threshold

        # Build full-length anomaly column (fill False for dry days)
        df["anomaly"] = False
        df.loc[nonzero_mask, "anomaly"] = anomaly_mask
    else:
        df["anomaly"] = False
        st.warning("Not enough non-zero precipitation values for LOF analysis.")

    anomalies = df[df["anomaly"]]

    # Plot
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df["time"], y=df["precipitation"],
        mode="lines", name="Precipitation (mm)",
        line=dict(width=1.2, color="blue"),
        hovertemplate="%{x}<br>Precip: %{y:.2f} mm<extra></extra>"
    ))

    fig2.add_trace(go.Scatter(
        x=anomalies["time"], y=anomalies["precipitation"],
        mode="markers", name=f"Anomalies ({len(anomalies)})",
        marker=dict(color="red", size=6, symbol="x"),
        hovertemplate="Anomaly<br>%{x}<br>Precip: %{y:.2f} mm<extra></extra>"
    ))

    fig2.update_layout(
        title=f"Precipitation — LOF Anomaly Detection ({city}, {year})",
        xaxis_title="Time", yaxis_title="Precipitation (mm)",
        template="plotly_white",
        hovermode="x unified",
        height=450
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### Anomaly Summary")
    st.markdown(f"**Number of anomalies:** {len(anomalies)}")
    st.dataframe(anomalies[["time", "precipitation"]].head(10))


