import sys
import streamlit as st
import pandas as pd
import validators

sys.path.append("..")
from DB.Database import Database

st.title('Main')
st.sidebar.title('Main')

db = Database()
df = pd.DataFrame()

if 'query' not in st.session_state:
    st.session_state['query'] = ""
if 'language' not in st.session_state:
    st.session_state['language'] = ""
if 'page' not in st.session_state:
    st.session_state['page'] = 1


with st.form(key="search", clear_on_submit=False):
    language = st.radio("Please select a language", ("german", "english"))
    search_string = st.text_input("Search", key='query_input')
    submitted = st.form_submit_button("Submit")

if submitted and not search_string == "":
    st.session_state['query'] = search_string
    st.session_state['language'] = language
    st.session_state['page'] = 1

def update_dataframe(page):
    df = pd.DataFrame(db.search_db_with_query(st.session_state['query'], st.session_state['language'], page=st.session_state['page']))
    return df

if not st.session_state['query'] == "":
    st.markdown("Results for `" + st.session_state['query'] + "`:")
    col1, col2, col3 = st.columns(3)
    with col1:
        prevpage = st.button("Back")
        if prevpage:
            if st.session_state['page'] > 1:
                st.session_state['page'] = st.session_state['page'] - 1

    with col2:
        nextpage = st.button("Next")
        if nextpage:
            st.session_state['page'] = st.session_state['page'] + 1

    with col3:
        st.write("Page: " + str(st.session_state['page']))
    st.dataframe(update_dataframe(st.session_state['page']))
