import sys

import pandas as pd
import streamlit as st
import validators
sys.path.append("..")
from DB.Database import Database

st.sidebar.title('Admin')
st.title('Admin')

db = Database()

with st.form(key="entry", clear_on_submit=True):
    url = st.text_input("URL")
    submitted = st.form_submit_button("Submit")
if submitted:
    if validators.url(url):
        if db.add_start_url(url):
            st.sidebar.success("Added entry into Database")
        else:
            st.sidebar.error("An Error occured. Please try again later")
    else:
        st.sidebar.error("URL is not valid")

with st.expander("Start URLs", expanded=True):
    data = pd.DataFrame({'url': db.get_all_start_urls()})
    st.dataframe(data)
