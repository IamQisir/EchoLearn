import streamlit as st
import numpy as np
import pandas as pd
from time import sleep


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    username = st.text_input("Username", key="username")
    password = st.text_input("Password", key="password", type="password")
    if st.button("Log in"):
        if username == 'test' and password == 'test':
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.warning('Wrong username or password!')

def logout():
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()

login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Account": [logout_page],
        },
        position='sidebar'
    )
else:
    pg = st.navigation([login_page])

pg.run()
