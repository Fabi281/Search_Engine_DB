import sys

import pandas as pd
import streamlit as st
import validators
sys.path.append("..")
from DB.Database import Database

st.sidebar.title('Admin')
st.title('Admin')

db = Database()

with st.form(key="start_url", clear_on_submit=True):
    url = st.text_input("Add entrypoint URL")
    addUrl = st.form_submit_button("Insert")
if addUrl:
    if validators.url(url):
        if db.insert_single_into_single_table(Database.Table.starturls.value, (url,)):
            st.sidebar.success("Added entry into Database")
        else:
            st.sidebar.error("An Error occured. Please try again later")
    else:
        st.sidebar.error("URL is not valid")

with st.expander("Entrypoint URLs"):
    data = db.get_all_start_urls()
    for entry in data:
        entry["checked"] = st.checkbox(entry["url"])
    deletedUrl = st.button("Delete Selected", key="del_url")
    if deletedUrl:
        for entry in data:
            if entry["checked"]:
                db.delete_from_table(Database.Table.starturls.value, entry["id"])
        st.experimental_rerun()

with st.form(key="allowed_domain", clear_on_submit=True):
    domain = st.text_input("Add allowlisted domain")
    submittedDomain = st.form_submit_button("Submit")
if submittedDomain:
    if db.insert_single_into_single_table(Database.Table.alloweddomains.value, (domain,)):
        st.sidebar.success("Added entry into Database")
    else:
        st.sidebar.error("An Error occured. Please try again later")

with st.expander("Allowlisted domains"):
    data = db.get_all_allowed_domains()
    for entry in data:
        entry["checked"] = st.checkbox(entry["domain"])
    deletedDomain = st.button("Delete Selected", key="del_domain")
    if deletedDomain:
        for entry in data:
            if entry["checked"]:
                db.delete_from_table(Database.Table.alloweddomains.value, entry["id"])
        st.experimental_rerun()
