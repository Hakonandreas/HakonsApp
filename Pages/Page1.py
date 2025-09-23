import streamlit as st
import pandas as pd


# Import data from CSV
df = pd.read_csv("open-meteo-subset.csv")

st.subheader("Data med radvise linjediagrammer")

# Bygg column_config slik at alle parametere får LineChartColumn
column_config = {}
for col in df.columns:
    if col.lower() not in ["time", "timestamp", "date"]:  # behold tid som vanlig tekst
        column_config[col] = st.column_config.LineChartColumn(
            label=col,
            y_min=df[col].min(),
            y_max=df[col].max(),
        )

st.dataframe(
    df,
    column_config=column_config,
    hide_index=True,
)


