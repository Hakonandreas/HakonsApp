import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px

# Connect to MongoDB
uri = st.secrets["mongodb"]["uri"]
client = MongoClient(uri)
db = client.elhub_db


# Load data
collection = db.production
data = list(collection.find())
df = pd.DataFrame(data)
'''
# Drop MongoDB's automatic _id column if present
if "_id" in df.columns:
    df = df.drop(columns=["_id"])'''


# For example:
# df.rename(columns={"pricearea": "pricearea", "productiongroup": "productiongroup", "quantitykwh": "quantitykwh"}, inplace=True)

# Split the layout into two columns
left, right = st.columns(2)

# LEFT COLUMN
with left:
    st.subheader("Price Area Overview")

    # Let the user select a price area
    price_areas = df["pricearea"].unique()
    chosen_area = st.radio("Select a price area:", options=sorted(price_areas))

    # Filter and aggregate like in my notebook
    area_data = (
        df[df["pricearea"] == chosen_area]
        .groupby("productiongroup", as_index=False)["quantitykwh"]
        .sum()
        .rename(columns={"quantitykwh": "total_quantity"})
    )

    # Create pie chart
    fig = px.pie(
        area_data,
        names="productiongroup",
        values="total_quantity",
        title=f"Total Production in {chosen_area} (2021)",
        hole=0.0
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

