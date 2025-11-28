import streamlit as st
import pandas as pd
from statsmodels.tsa.seasonal import STL
from scipy.signal import spectrogram
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from functions.elhub_utils import load_elhub_data

df = load_elhub_data()

# Use the chosen area from session_state
pricearea = st.session_state["chosen_area"]

st.title("STL & Spectrogram Analysis")
st.markdown(f"### Current price area: `{pricearea}`")

# Tabs
tab1, tab2 = st.tabs(["📈 STL Decomposition", "🎛 Spectrogram"])

# TAB 1 — STL DECOMPOSITION
with tab1:
    st.subheader("Seasonal-Trend decomposition using LOESS (STL)")

    # Production group selection and STL default parameters
    production_groups = sorted(df["productiongroup"].unique())
    productiongroup = st.selectbox("Select production group:", options=production_groups)

    period = st.number_input("Period (hours)", value=24 * 7)
    seasonal = st.number_input("Seasonal smoother", value=13)
    trend = st.number_input("Trend smoother", value=int(period * 2 + 1))
    robust = st.checkbox("Robust fitting", value=True)

    # Filter data and prepare for STL
    dfa = (
        df[(df["pricearea"] == pricearea) & (df["productiongroup"] == productiongroup)]
        .set_index("starttime")[["quantitykwh"]]
        .resample("h")
        .mean()
        .interpolate()
    )

    # Run STL decomposition
    if dfa.empty:
        st.warning("No data found for the selected combination.")
    else:
        stl = STL(dfa["quantitykwh"], period=period, seasonal=seasonal, trend=trend, robust=robust)
        res = stl.fit()

        # Create subplots
        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("Observed", "Trend", "Seasonal", "Residual"),
        )

        fig.add_trace(go.Scatter(x=dfa.index, y=dfa["quantitykwh"], line=dict(color="steelblue")), row=1, col=1)
        fig.add_trace(go.Scatter(x=dfa.index, y=res.trend, line=dict(color="royalblue")), row=2, col=1)
        fig.add_trace(go.Scatter(x=dfa.index, y=res.seasonal, line=dict(color="seagreen")), row=3, col=1)
        fig.add_trace(go.Scatter(x=dfa.index, y=res.resid, mode="markers", marker=dict(color="firebrick", size=4)), row=4, col=1)

        fig.update_layout(
            height=800,
            title=f"STL Decomposition — {productiongroup.capitalize()} ({pricearea})",
            showlegend=False,
            template="plotly_white",
        )
        fig.update_xaxes(title_text="Date", row=4, col=1)
        fig.update_yaxes(title_text="kWh")

        st.plotly_chart(fig, width='stretch')

# TAB 2 — SPECTROGRAM
with tab2:
    st.subheader("Spectrogram")

    productiongroup = st.selectbox(
        "Select production group for spectrogram:",
        options=production_groups,
        key="spec_group"
    )
    window_length = st.number_input("Window length (hours)", value=168)
    overlap = st.slider("Window overlap", min_value=0.0, max_value=0.9, value=0.5, step=0.1)

    # Filter and prepare data
    dfa = (
        df[(df["pricearea"] == pricearea) & (df["productiongroup"] == productiongroup)]
        .set_index("starttime")[["quantitykwh"]]
        .resample("h")
        .mean()
        .interpolate()
    )

    # Compute and plot spectrogram
    if dfa.empty:
        st.warning("No data available for this selection.")
    else:
        signal = dfa["quantitykwh"].values
        fs = 1.0  # samples/hour
        nperseg = int(window_length)
        noverlap = int(window_length * overlap)
        freqs, times, Sxx = spectrogram(signal, fs=fs, nperseg=nperseg, noverlap=noverlap)
        Sxx_dB = 10 * np.log10(Sxx + 1e-10)
        times_dt = dfa.index[0] + pd.to_timedelta(times, unit="h")

        fig_spec = go.Figure(
            data=go.Heatmap(
                z=Sxx_dB,
                x=times_dt,
                y=freqs,
                colorscale="Viridis",
                colorbar=dict(title="Power (dB)"),
            )
        )

        fig_spec.update_layout(
            title=f"Spectrogram — {productiongroup.capitalize()} ({pricearea})",
            xaxis_title="Time",
            yaxis_title="Frequency (cycles/hour)",
            template="plotly_white",
            height=700,
        )

        st.plotly_chart(fig_spec, use_container_width=True)
