import pandas as pd
import streamlit as st

# Import data
df = pd.read_csv("open-meteo-subset.csv")

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

# No custom y-limits – one table only
st.dataframe(
    chart_df,
    column_config={
        "Parameter": "Parameter",
        "Values": st.column_config.LineChartColumn("Målinger (første måned)")
    },
    hide_index=True,
)
