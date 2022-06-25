import sys
import streamlit as st
import pandas as pd

sys.path.append("..")
from DB.Database import Database

st.title('Main')
st.sidebar.title('Main')

db = Database()
df = pd.DataFrame()
columns_titles = ["title","url","rank"]

if 'query' not in st.session_state:
    st.session_state['query'] = ""
if 'language' not in st.session_state:
    st.session_state['language'] = ""
if 'page' not in st.session_state:
    st.session_state['page'] = 1

with st.form(key="search", clear_on_submit=False):
    language = st.radio("Please select a language", ("german", "english"))
    search_string = st.text_input("Search", key='query_input')
    weight = 0.8
    with st.expander("Advanced options"):
        weight = st.slider("Weight of TF-IDF", 0.0, 1.0, weight, key='weight_input')
    submitted = st.form_submit_button("Submit")

if submitted and not search_string == "":
    st.session_state['query'] = search_string
    st.session_state['language'] = language
    st.session_state['page'] = 1


def update_dataframe():
    df = pd.DataFrame(db.search_db_with_query(query=st.session_state['query'],
                                              language=st.session_state['language'],
                                              weight_tfidf=weight,
                                              page=st.session_state['page']))
    return df

def style_table(styler):
    styler.set_table_styles([dict(selector='th', props=[('text-align', 'left')])])
    styler.format(dict(url= lambda x: f'<a href="{x}">{x}</a>'))

    return styler

def print_urls(df):
    df = df.reindex(columns=columns_titles)
    df = df.style.pipe(style_table)
    st.write(df.to_html(escape = False, col_space=dict(title=300)), unsafe_allow_html = True)

if not st.session_state['query'] == "":
    with st.expander("Word suggestions"):
        for word in db.predict_words_for_query(st.session_state['query']):
            st.markdown(" - "+word)

    st.markdown("Results for `" + st.session_state['query'] + "`:")
    col1, col2, col3 = st.columns(3)
    with col1:
        prev_page = st.button("Back")
        if prev_page:
            if st.session_state['page'] > 1:
                st.session_state['page'] = st.session_state['page'] - 1

    with col2:
        next_page = st.button("Next")
        if next_page:
            st.session_state['page'] = st.session_state['page'] + 1

    with col3:
        st.write("Page: " + str(st.session_state['page']))
    
    print_urls(update_dataframe())
