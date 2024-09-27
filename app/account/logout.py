import streamlit as st
import yaml
from yaml.loader import SafeLoader


def logout():
    st.session_state['authentication_status'] = None
    st.rerun()
