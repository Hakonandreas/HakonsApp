import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import toml


# Pages/some_page.py
import streamlit as st
from pymongo import MongoClient

mongo_uri = st.secrets["mongodb"]["uri"]
client = MongoClient(mongo_uri)
db = client["my_database"]
collection = db["my_collection"]

st.write(f"Loaded {collection.count_documents({})} documents")
