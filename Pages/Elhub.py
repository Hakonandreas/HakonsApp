import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import toml


uri = st.secrets["mongodb"]["uri"]
client = MongoClient(uri)
db = client.get_database()  # defaults to the database in the URI
collection = db["your_collection_name"]

data = list(collection.find())
st.write(data)
