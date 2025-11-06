import streamlit as st
from functions.weather_utils import get_city_from_area, download_era5_data

chosen_area = st.session_state["chosen_area"]
city, lat, lon = get_city_from_area(chosen_area)
year = 2021

st.write(f"**Price Area:** {chosen_area} → **City:** {city} ({lat:.2f}, {lon:.2f})")
st.write(f"Downloading ERA5 data for **{year}**...")

df = download_era5_data(lat, lon, year)

st.success(f"✅ Successfully downloaded ERA5 data for {city} ({year})!")


# Show imported data
st.subheader("Imported Data Table")
st.dataframe(df)

# Convert time column
df["time"] = pd.to_datetime(df["time"])
first_month_mask = df["time"].dt.month == df["time"].iloc[0].month
first_month_df = df.loc[first_month_mask]

# Transpose so each parameter is a row
df_t = first_month_df.drop(columns=["time"]).transpose()

# Build chart dataframe
chart_df = pd.DataFrame({
    "Parameter": df_t.index,
    "Values": df_t.values.tolist()
})

st.subheader("First Month Data (Row-wise Line Chart, no y-limits)")

st.dataframe(
    chart_df,
    column_config={
        "Parameter": "Parameter",
        "Values": st.column_config.LineChartColumn("Målinger (første måned)")
    },
    hide_index=True,
)
