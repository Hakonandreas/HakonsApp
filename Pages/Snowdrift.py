import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Import the core functions (make sure Snow_drift.py has no matplotlib, only computations)
from functions.Snow_drift import compute_yearly_results, compute_average_sector

st.set_page_config(page_title="Snow Drift Calculator", layout="wide")
st.title("Snow Drift Calculation and Wind Rose")

# ---------------- Session State ----------------
if "chosen_area" not in st.session_state:
    st.session_state["chosen_area"] = None

# ---------------- Map Selection ----------------
st.subheader("Select a location")
# For demonstration, we use st.map with points (replace with your actual selection logic)
map_df = pd.DataFrame(
    [[60.57, 7.60]],
    columns=["lat", "lon"]
)
st.map(map_df)

if st.button("Select this location"):
    st.session_state["chosen_area"] = map_df.iloc[0].to_dict()
    st.success(f"Location selected: {st.session_state['chosen_area']}")

# ---------------- Year Range Selection ----------------
st.subheader("Select year range")
start_year, end_year = st.slider(
    "Choose start and end year",
    2000, 2025, (2015, 2020)
)

# ---------------- Check prerequisites ----------------
if st.session_state["chosen_area"] is None:
    st.warning("Please select a location first!")
    st.stop()

# ---------------- Load meteorological data ----------------
filename = "open-meteo-60.57N7.60E1212m.csv"
df = pd.read_csv(filename, skiprows=3)
df['time'] = pd.to_datetime(df['time'])

# ---------------- Snow transport parameters ----------------
T = 3000
F = 30000
theta = 0.5

# ---------------- Compute results ----------------
yearly_df = compute_yearly_results(df, T, F, theta, start_year, end_year)
if yearly_df.empty:
    st.warning("No data available for the selected year range.")
    st.stop()

overall_avg = yearly_df['Qt (kg/m)'].mean()

st.subheader("Yearly Average Snow Drift (Qt)")
st.dataframe(
    yearly_df.assign(**{"Qt (tonnes/m)": yearly_df['Qt (kg/m)']/1000}),
    use_container_width=True
)
st.write(f"**Overall average Qt:** {overall_avg/1000:.1f} tonnes/m")

# ---------------- Compute average sector values ----------------
avg_sectors = compute_average_sector(df, start_year, end_year)

# ---------------- Plotly Wind Rose ----------------
def plot_rose_plotly(avg_sector_values, overall_avg):
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    avg_tonnes = [v/1000.0 for v in avg_sector_values]

    fig = go.Figure(go.Barpolar(
        r=avg_tonnes,
        theta=directions,
        width=[22.5]*16,
        marker_color='skyblue',
        marker_line_color='black',
        marker_line_width=1,
        opacity=0.8
    ))

    fig.update_layout(
        title=f'Average Directional Snow Transport<br>Overall Qt: {overall_avg/1000:.1f} tonnes/m',
        polar=dict(
            radialaxis=dict(title='Snow Transport (tonnes/m)'),
            angularaxis=dict(direction='clockwise', rotation=90)
        ),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Average Directional Snow Transport (Wind Rose)")
plot_rose_plotly(avg_sectors, overall_avg)
