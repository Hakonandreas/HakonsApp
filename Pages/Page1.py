import pandas as pd
import streamlit as st

# Import data
df = pd.read_csv("open-meteo-subset.csv")

# Vis importerte data
st.subheader("Imported Data Table")
st.dataframe(df)

# ---- Hent ut første måned ----
df["time"] = pd.to_datetime(df["time"])
first_month_mask = df["time"].dt.month == df["time"].iloc[0].month
first_month_df = df.loc[first_month_mask]

# Transponer: rad = parameter, values = liste med målinger gjennom måneden
df_t = first_month_df.drop(columns=["time"]).transpose()

chart_df = pd.DataFrame({
    "Parameter": df_t.index,
    "Values": df_t.values.tolist()
})

# Tilpassede y-limits for utvalgte parametere
custom_limits = {
    "precipitation (mm)": (0, first_month_df["precipitation (mm)"].max()),
    "wind_speed_10m (m/s)": (0, first_month_df["wind_speed_10m (m/s)"].max()),
    "wind_gusts_10m (m/s)": (0, first_month_df["wind_gusts_10m (m/s)"].max()),
}





# Show combined table with per-row line charts and custom y-limits using st.data_editor
st.subheader("First Month Data (Combined Table with Custom Line Charts)")

def get_line_chart_column(param):
    if param in custom_limits:
        ymin, ymax = custom_limits[param]
    else:
        ymin, ymax = int(df_t.min().min()), int(df_t.max().max())
    return st.column_config.LineChartColumn(
        f"Målinger (første måned)", y_min=ymin, y_max=ymax
    )

column_config = {
    "Parameter": st.column_config.TextColumn("Parameter"),
    "Values": [get_line_chart_column(param) for param in chart_df["Parameter"]]
}

st.data_editor(
    chart_df,
    column_config=column_config,
    hide_index=True,
    height=600,
)

