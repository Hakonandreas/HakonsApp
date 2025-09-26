import streamlit as st

st.title("Project IND320")
st.write(
    "My Streamlit app for IND320"
)
'''
st.sidebar.title("Navigation")

# List of page names (must match filenames without .py)
pages = ["Home", "Page1", "Page2", "Page3", "Page4"]
choice = st.sidebar.radio("Go to", pages)

# Load selected page
if choice == "Home":
    st.write("Welcome to the Home page!")
else:
    # Dynamically run the selected page from Pages folder
    with open(f"Pages/{choice}.py", "r") as f:
        code = f.read()
    exec(code, globals())'''
