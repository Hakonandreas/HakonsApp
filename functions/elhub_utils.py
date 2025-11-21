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


@st.cache_data
def load_elhub_data():
    """Load and preprocess Elhub production data."""
    client = get_mongo_client()
    db = client.elhub_db

    # Collections
    prod_collection = db.production

    # Load production
    prod_data = list(prod_collection.find())
    prod_df = pd.DataFrame(prod_data)
    if prod_df.empty:
        raise ValueError("No data found in the 'production' collection.")
    prod_df["starttime"] = pd.to_datetime(prod_df["starttime"])
    prod_df["month"] = prod_df["starttime"].dt.strftime("%Y-%m")
    prod_df["date"] = prod_df["starttime"].dt.date
        
    return prod_df

@st.cache_data
def load_elhub_consumption():
    """Load and preprocess Elhub consumption data."""
    client = get_mongo_client()
    db = client.elhub_db

    # Collection
    cons_collection = db.consumption

    # Load consumption
    cons_data = list(cons_collection.find())
    cons_df = pd.DataFrame(cons_data)
    if cons_df.empty:
        raise ValueError("No data found in the 'consumption' collection.")
    cons_df["starttime"] = pd.to_datetime(cons_df["starttime"])
    cons_df["month"] = cons_df["starttime"].dt.strftime("%Y-%m")
    cons_df["date"] = cons_df["starttime"].dt.date

    return cons_df