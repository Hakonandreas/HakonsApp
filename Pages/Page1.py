import streamlit as st
import pandas as pd

st.title("Page 1")

# Import data from CSV
df = pd.read_csv("open-meteo-subset.csv")

st.subheader("Imported Data Table")
st.dataframe(df)

# Display a line chart for the first month of the data series (assuming first row is first month)
st.subheader("First Month Data (Row-wise Line Chart)")
first_month = df.iloc[0]
chart_data = pd.DataFrame({
	'Column': df.columns,
	'Value': first_month.values
})
st.line_chart(chart_data.set_index('Column'))


