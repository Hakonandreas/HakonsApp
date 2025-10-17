import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import toml

# Correctly access the 'uri' key inside the 'mongodb' section
uri = st.secrets["mongodb"]["uri"]


client = pymongo.MongoClient(uri)

# Now you can work with your database
db = client.test
st.write("Successfully connected to MongoDB!")