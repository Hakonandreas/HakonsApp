import streamlit as st
from functions.elhub_utils import load_elhub_data, load_elhub_consumption
from functions.weather_utils import download_era5_data

st.title("Energy & Meteorology Data Explorer")

# --- CATEGORY SELECTION -----------------------------------------------------
col1, col2 = st.columns([1, 3])
with col1:
    data_type = st.radio(
        "Select data type:",
        ["Production", "Consumption"],
        horizontal=True
    )

st.write("---")

# --- LOAD DATA BASED ON SELECTION ------------------------------------------
data = None
variables = []

if data_type == "Consumption":
    try:
        data = load_elhub_consumption()
        variables = data.columns.tolist()
    except Exception as e:
        st.error(f"Could not load consumption data: {e}")

elif data_type == "Production":
    try:
        data = load_elhub_data()

        # production datasets sometimes only include metadata → check columns
        if data is not None and len(data.columns) > 1:
            variables = data.columns.tolist()
        else:
            variables = []
    except Exception as e:
        st.error(f"Could not load production data: {e}")

# --- UI WHEN DATA IS NOT AVAILABLE -----------------------------------------
if data is None:
    st.warning("No data available for this choice.")
    st.stop()

if len(variables) == 0:
    st.warning("No variables available for this selection.")
    st.stop()

# --- VARIABLE SELECTORS SIDE BY SIDE ---------------------------------------
st.subheader("Select variable(s)")

left, right = st.columns(2)

with left:
    selected_energy_var = st.selectbox(
        "Energy variable:",
        variables
    )

with right:
    meteo_choice = st.checkbox("Load meteorology variable?")

if meteo_choice:
    meteo_var = st.selectbox(
        "Meteorology variable:",
        ["temperature", "wind_speed", "solar_radiation"],
    )

# --- DISPLAY PREVIEW --------------------------------------------------------
st.write("### Data preview")
st.dataframe(data.head())
