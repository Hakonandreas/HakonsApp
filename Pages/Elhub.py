import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import toml

# Page title
st.title("Electricity Production")

# Connect to MongoDB

secret_path = "/workspaces/HakonsApp/.streamlit/secrets.toml"
uri = toml.load(open(secret_path))['mongodb']['uri']
#uri = st.secrets['mongodb']['uri']
client = MongoClient(uri)
db = client.get_database()
collection = db['production']

# Load data
data = list(collection.find())
df = pd.DataFrame(data)

# Split page into two columns
left, right = st.columns(2)

# Left column: select price area
with left:
    price_areas = df["pricearea"].unique().tolist()
    selected_area = st.radio("Select a price area:", price_areas)

    # Filter data for selected price area
    area_data = df[df["pricearea"] == selected_area]

    # Group by productiongroup and sum the quantitykwh
    pie_data = area_data.groupby("productiongroup", as_index=False)["quantitykwh"].sum()

    # Create interactive pie chart
    fig = px.pie(
        pie_data,
        names="productiongroup",
        values="quantitykwh",
        title=f"Production distribution in {selected_area}",
    )

    # Display chart
    st.plotly_chart(fig, use_container_width=True)
