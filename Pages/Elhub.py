import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px

# Connect to MongoDB
uri = st.secrets["mongodb"]["uri"]
client = MongoClient(uri)
db = client.elhub_db


# --- Load data from MongoDB ---
# Replace 'elhub_data' with your actual collection name
collection = db.production
data = list(collection.find())
df = pd.DataFrame(data)

# Drop MongoDB's automatic _id column if present
if "_id" in df.columns:
    df = df.drop(columns=["_id"])

# --- Split view into two columns ---
left, right = st.columns(2)

# ===== LEFT COLUMN =====
with left:
    st.subheader("Price Area Overview")

    # Let the user select a price area
    price_areas = df["PriceArea"].unique()
    selected_area = st.radio("Select a price area:", options=price_areas)

    # Filter data for the selected area
    area_data = df[df["PriceArea"] == selected_area]

    # Create a pie chart (for example, distribution by production group)
    fig_pie = px.pie(
        area_data,
        names="ProductionGroup",   # adjust column name if different
        values="Value",            # adjust column name if different
        title =f"Production Distribution in {selected_area}"
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)
