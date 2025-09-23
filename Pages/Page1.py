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



# Show main table
st.subheader("First Month Data (Row-wise Line Chart)")
st.dataframe(
    chart_df,
    column_config={
        "Parameter": "Parameter",
        "Values": st.column_config.LineChartColumn(
            "Målinger (første måned)",
            y_min=int(df_t.min().min()),
            y_max=int(df_t.max().max()),
        ),
    },
    hide_index=True,
)

# Show individual line charts for each parameter with custom axes
st.subheader("First Month Data (Custom y-limits per parameter)")
for i, row in chart_df.iterrows():
    param = row["Parameter"]
    values = row["Values"]
    if param in custom_limits:
        ymin, ymax = custom_limits[param]
    else:
        ymin, ymax = int(df_t.min().min()), int(df_t.max().max())
    st.write(f"**{param}**")
    st.line_chart(pd.DataFrame({param: values}), y_min=ymin, y_max=ymax)
