import streamlit as st
import pandas as pd


# Import data from CSV
df = pd.read_csv("open-meteo-subset.csv")

st.subheader("Imported Data Table")
st.dataframe(df)

# Show row-wise line chart for the first month
st.subheader("First Month Data (Row-wise Line Chart)")

# Take first row of the dataframe (assumed first month)
first_month = df.iloc[0]

# Reshape: each column becomes a row
chart_data = pd.DataFrame({
    "Column": df.columns,
    "Value": first_month.values
})

# Display as a table
st.table(chart_data)

# Display as a line chart (row-wise)
st.line_chart(chart_data.set_index("Column"))


