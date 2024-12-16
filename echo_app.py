# echo_app.py

import streamlit as st
from time import sleep
import base64
from streamlit_extras.customize_running import center_running
from app_state import AppState
from models.user import User
from utils.state_manager import initialize_state, StateManager
from typing import Dict, List, Any

def setup_page_config():
    """Setup initial page configuration"""
    st.set_page_config(layout="wide", page_icon="logo/done_all.png")
    
    # Set logo in sidebar and main page
    st.logo(image="logo/EchoLearn.png", icon_image="logo/EchoLearn.png")
    
    # Custom CSS for logo styling
    st.markdown(
        """
        <style>
            div[data-testid="stSidebarHeader"] > img, div[data-testid="collapsedControl"] > img {
                height: 6rem;
                width: auto;
            }
            
            div[data-testid="stSidebarHeader"], div[data-testid="stSidebarHeader"] > *,
            div[data-testid="collapsedControl"], div[data-testid="collapsedControl"] > * {
                display: flex;
                align-items: center;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

def display_centered_gif():
    """Display centered EchoLearn gif"""
    _, cent_co, _ = st.columns([0.2, 0.7, 0.1])
    with cent_co:
        with open("logo/EchoLearn.gif", "rb") as f:
            contents = f.read()
            data_url = base64.b64encode(contents).decode("utf-8")
        st.markdown(
            f'<img src="data:image/gif;base64,{data_url}" alt="cat gif" class="center">',
            unsafe_allow_html=True,
        )

def login(app_state: AppState):
    """Handle user login"""
    display_centered_gif()
    st.markdown("# EchoLearnへよこそう! 😍 発音を上達しましょう!")
    
    with st.form(key='password_form'):
        username = st.text_input("ユーザー名", key="username")
        password = st.text_input("パスワード", key="password", type="password")
        submit_button = st.form_submit_button(label='ログイン')

        if submit_button:
            user = User.login(username, password)
            if user:
                app_state.set_user(user)
                app_state.logged_in = True
                # 注意这里，直接使用模块名而不是文件路径
                st.switch_page("views.learning_view")

def register(app_state: AppState):
    """Handle user registration"""
    display_centered_gif()
    st.markdown("# 新規登録して利用できます! 😉")
    
    with st.form(key='register_form'):
        username = st.text_input("ユーザー名", key="username")
        password = st.text_input("パスワード", key="password", type="password")
        submit_button = st.form_submit_button(label='新規登録')

        if submit_button:
            user = User.register(username, password)
            if user:
                app_state.set_user(user)
                app_state.logged_in = True
                st.switch_page("views.learning_view")

def logout(app_state: AppState):
    """Handle user logout"""
    app_state.clear_state()
    st.rerun()

def initialize_app_state() -> AppState:
    """Initialize or get existing app state"""
    if 'app_state' not in st.session_state:
        app_state = AppState()
        st.session_state.app_state = app_state
    return st.session_state.app_state

def setup_navigation(app_state: AppState):
    """Setup navigation based on login state"""
    
    if app_state.logged_in:
        pages = {
            "アカウント": [
                st.Page(
                    logout,  # 直接使用函数名
                    title="ログアウト",
                    icon=":material/logout:"
                )
            ],
            "ラーニング": [
                st.Page(
                    "views/learning_view",  # 不需要.py后缀
                    title='エコーラーニング',
                    icon="🔥"
                )
            ]
        }
    else:
        pages = {
            "アカウント": [
                st.Page(
                    login,  # 直接使用函数名
                    title="ログイン",
                    icon=":material/login:"
                ),
                st.Page(
                    register,  # 直接使用函数名
                    title="新規登録",
                    icon=":material/login:"
                )
            ]
        }
    
    nav = st.navigation(pages)
    return nav

def main():
    # Setup page configuration
    setup_page_config()
    
    # Initialize app state
    app_state = initialize_state()
    
    # Setup navigation
    pg = setup_navigation(app_state)
    
    # Set sidebar header
    st.sidebar.header("EchoLearnへようこそ! 😊")
    
    # Run the selected page
    pg.run()

if __name__ == "__main__":
    main()