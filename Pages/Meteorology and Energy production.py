import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from functions.elhub_utils import load_elhub_data, load_elhub_consumption
from functions.weather_utils import download_era5_data

# ---------------------------------------------------------
# Sliding Window Correlation function
# ---------------------------------------------------------
def sliding_window_corr(series1, series2, window, lag):
    """
    Compute sliding window correlation with lag.
    Lag > 0 shifts meteorology BACKWARD (met at t-lag vs energy at t).
    """
    s1 = series1.shift(lag)  # shift meteorology
    return s1.rolling(window, center=True).corr(series2)


# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------
st.title("📈 Sliding Window Correlation Explorer")
st.markdown("""
Explore relationships between **meteorological conditions** and  
**energy production/consumption** with adjustable **window** and **lag**.
""")

# Load data
prod_df = load_elhub_data()
cons_df = load_elhub_consumption
weather_df = download_era5_data()

# Merge on date
merged = pd.merge(weather_df, prod_df, on="date", how="inner")
merged = pd.merge(merged, cons_df, on="date", suffixes=("_prod", "_cons"))

# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
st.sidebar.header("Controls")

met_vars = [c for c in weather_df.columns if c not in ["date", "time"]]
energy_vars = [c for c in merged.columns if c not in weather_df.columns and c not in ["date", "starttime"]]

met_var = st.sidebar.selectbox("Meteorological variable", met_vars)
energy_var = st.sidebar.selectbox("Energy variable", energy_vars)

window = st.sidebar.slider("Window size (days)", 5, 120, 45)
lag = st.sidebar.slider("Lag (days)", -30, 30, 0)

# Extract series
s1 = merged[met_var]
s2 = merged[energy_var]

# Compute SWC
swc = sliding_window_corr(s1, s2, window, lag)

# ---------------------------------------------------------
# Plotly Visualization
# ---------------------------------------------------------
fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True,
    subplot_titles=(met_var, energy_var, "Sliding Window Correlation")
)

fig.add_trace(go.Scatter(y=s1, mode="lines", name=met_var), row=1, col=1)
fig.add_trace(go.Scatter(y=s2, mode="lines", name=energy_var), row=2, col=1)
fig.add_trace(go.Scatter(y=swc, mode="lines", name="SWC"), row=3, col=1)

fig.update_yaxes(title_text=met_var, row=1, col=1)
fig.update_yaxes(title_text=energy_var, row=2, col=1)
fig.update_yaxes(title_text="Correlation", range=[-1, 1], row=3, col=1)

fig.update_layout(height=900, showlegend=False)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# Interpretation section
# ---------------------------------------------------------
st.markdown("""
## 🔍 Interpretation Tips

Try playing with lags and window sizes:

- **Lag > 0**: Meteorology influences energy *in the future*  
- **Lag < 0**: Energy changes precede weather patterns (often noise)
- **Large window (80–120 days)**: long-term seasonal patterns  
- **Small window (5–20 days)**: acute responses, e.g., storms or cold snaps  

Look for correlations that  
- **drop sharply** during storms  
- **flip sign** around extreme cold or heat events  
- **increase** during stable temperature–demand relationships  

""")
