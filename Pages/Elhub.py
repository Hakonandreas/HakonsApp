import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import toml


# streamlit_app.py
import streamlit as st
from pymongo import MongoClient
import os
import toml

# -------------------------------
# Step 1: Load secrets safely
# -------------------------------

# Base folder of this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to .streamlit/secrets.toml
SECRETS_PATH = os.path.join(BASE_DIR, ".streamlit", "secrets.toml")

secrets = {}
if os.path.exists(SECRETS_PATH):
    secrets = toml.load(SECRETS_PATH)
else:
    st.warning(f"Secrets file not found at {SECRETS_PATH}. Using st.secrets if available.")
    if hasattr(st, "secrets"):
        secrets = st.secrets  # fallback to Streamlit default

# -------------------------------
# Step 2: Get Mongo URI
# -------------------------------
try:
    mongo_uri = secrets["mongodb"]["uri"]
except KeyError:
    st.error("MongoDB URI not found in secrets!")
    st.stop()  # Stop execution

# -------------------------------
# Step 3: Connect to MongoDB
# -------------------------------
try:
    client = MongoClient(mongo_uri)
    client.admin.command("ping")  # Test connection
    st.success("Connected to MongoDB!")
except Exception as e:
    st.error(f"Failed to connect to MongoDB: {e}")
    st.stop()

# -------------------------------
# Step 4: Your page logic
# -------------------------------
db = client["my_database"]
collection = db["my_collection"]

st.write(f"Loaded {collection.count_documents({})} documents.")

# Example dynamic page loading
choice = st.selectbox("Select page", ["page1", "page2"])
page_path = os.path.join(BASE_DIR, "Pages", f"{choice}.py")

if os.path.exists(page_path):
    with open(page_path, "r") as f:
        code = f.read()
    exec(code, {"st": st, "secrets": secrets, "client": client})
else:
    st.warning(f"Page file not found: {page_path}")
