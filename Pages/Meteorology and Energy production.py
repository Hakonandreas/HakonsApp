import streamlit as st
from functions.elhub_utils import load_elhub_data, load_elhub_consumption
from functions.weather_utils import download_era5_data

st.title("Energy & Meteorology Data Explorer")

# ---------------------------------------------------------
# CATEGORY SELECTION (side-by-side)
# ---------------------------------------------------------
colA, colB = st.columns([1, 4])
with colA:
    data_type = st.radio(
        "Data Type",
        ["Production", "Consumption"],
        horizontal=True
    )

st.write("---")

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
data = None

if data_type == "Consumption":
    try:
        data = load_elhub_consumption()
    except Exception as e:
        st.error(f"Failed to load consumption data: {e}")
        st.stop()

elif data_type == "Production":
    try:
        data = load_elhub_data()
        # Remove _id column if present
        if "_id" in data.columns:
            data = data.drop(columns=["_id"])
    except Exception as e:
        st.error(f"Failed to load production data: {e}")
        st.stop()

if data is None or data.empty:
    st.warning("No data available for the selected category.")
    st.stop()

energy_vars = data.columns.tolist()

# ---------------------------------------------------------
# LOAD METEOROLOGY DATA (always)
# ---------------------------------------------------------
try:
    meteo_df = download_era5_data()
    meteo_vars = meteo_df.columns.tolist()
except Exception as e:
    st.error(f"Failed to load meteorology data: {e}")
    st.stop()

# ---------------------------------------------------------
# VARIABLE SELECTORS (side-by-side)
# ---------------------------------------------------------
st.subheader("Select Variables")

col1, col2 = st.columns(2)

with col1:
    selected_energy_var = st.selectbox(
        "Energy Variable",
        energy_vars
    )

with col2:
    selected_meteo_var = st.selectbox(
        "Meteorology Variable",
        meteo_vars
    )

# ---------------------------------------------------------
# PREVIEW
# ---------------------------------------------------------
st.write("### Energy Data Preview")
st.dataframe(data[[selected_energy_var]].head())

st.write("### Meteorology Data Preview")
st.dataframe(meteo_df[[selected_meteo_var]].head())
