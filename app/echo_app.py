import json
import streamlit as st
from time import sleep
import base64
from streamlit_extras.customize_running import center_running
from user import User

st.set_page_config(layout="wide")

# Function to load user_info from a JSON file
def load_user_info():
    try:
        with open("database/all_users/users_info.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Function to save user_info to a JSON file
def save_user_info(user_info):
    with open("database/all_users/users_info.json", "w") as f:
        json.dump(user_info, f, indent=4)
    
# Load user_info as a global variable

st.logo(image="logo/EchoLearn.png", icon_image="logo/EchoLearn.png")
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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    _, cent_co, _ = st.columns([0.2, 0.7, 0.1])
    with cent_co:
        with open("logo/EchoLearn.gif", "rb") as f:
            contents = f.read()
            data_url = base64.b64encode(contents).decode("utf-8")
        st.markdown(
            f'<img src="data:image/gif;base64,{data_url}" alt="cat gif" class="center">',
            unsafe_allow_html=True,
        )
    st.markdown("# Welcome to Echo English Learning System! :D Please login.")
    username = st.text_input("Username", key="username")
    password = st.text_input("Password", key="password", type="password")
    if st.button("Log in"):
        user = User.login(username, password)
        if user:
            sleep(2)
            st.session_state.logged_in = True
            global learning_page
            st.switch_page(learning_page)
            
def register():
    _, cent_co, _ = st.columns([0.2, 0.7, 0.1])
    with cent_co:
        with open("logo/EchoLearn.gif", "rb") as f:
            contents = f.read()
            data_url = base64.b64encode(contents).decode("utf-8")
        st.markdown(
            f'<img src="data:image/gif;base64,{data_url}" alt="cat gif" class="center">',
            unsafe_allow_html=True,
        )
    st.markdown("# Please Register to use Echo :)")
    new_username = st.text_input("Username", key="new_username")
    new_password = st.text_input("Password", key="new_password", type="password")
    if st.button("Register"):
        new_user = User.register(new_username, new_password)
        if new_user:
            sleep(2)
            global login_page
            st.switch_page(login_page)

def logout():
    st.session_state.logged_in = False
    st.rerun()

# Account-related Page
login_page = st.Page(login, title="Log in", icon=":material/login:")
register_page = st.Page(register, title="Register", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

# Learning-related Page
learning_page = st.Page("../app/learn/final_gui_st.py", title='Learning Phase')
learn_st_page = st.Page("../app/learn_st.py", title='Mic Test')

# Set the navigation of sidebar
if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Account": [logout_page],
            "Learn": [learning_page, learn_st_page],
        }
    )
else:
    pg = st.navigation(
        {
            "Account": [login_page, register_page]
        }
    )

# Set the header of sidebar and run the main page
st.sidebar.header("Welcome to Echo English Learning System!")
pg.run()