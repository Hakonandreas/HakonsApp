import pandas as pd
import toml
from pymongo import MongoClient
import streamlit as st

# Functions for Elhub data handling

# MongoDB Connection
@st.cache_resource
def get_mongo_client():
    """Create and cache a MongoDB client connection."""
    secrets = st.secrets.get("mongodb", None)
    if not secrets:
        # For local testing
        secrets = toml.load("../../secrets.toml")["mongodb"]

    uri = secrets["uri"]
    client = MongoClient(uri)
    return client


# Load Elhub data
@st.cache_data
def load_elhub_data():
    """Load and preprocess Elhub production data."""
    client = get_mongo_client()
    db = client.elhub_db
    collection = db.production

    data = list(collection.find())
    df = pd.DataFrame(data)

    if df.empty:
        raise ValueError("No data found in the MongoDB 'production' collection.")

    df["starttime"] = pd.to_datetime(df["starttime"])
    df["month"] = df["starttime"].dt.strftime("%Y-%m")
    df["date"] = df["starttime"].dt.date

    return df
