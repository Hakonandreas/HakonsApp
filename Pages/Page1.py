import streamlit as st
import pandas as pd

st.title("Page 1")

# Import data from CSV
df = pd.read_csv("open-meteo-subset.csv")

st.subheader("Imported Data Table")
st.dataframe(df)

# Lag to kolonner
col1, col2 = st.columns([1, 1])  # Du kan justere forholdet, f.eks. [2, 1] for bredere tabell

with col1:
    st.dataframe(df)

with col2:
    st.subheader("First Month Data (Line Chart)")
    first_month = df.iloc[0]
    chart_data = pd.DataFrame({
        'Month': df.columns,
        'Value': first_month.values
    })
    st.line_chart(chart_data.set_index('Month'))

