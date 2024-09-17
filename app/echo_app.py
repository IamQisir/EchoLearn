import json
import streamlit as st
from time import sleep
import base64

st.set_page_config(layout="wide")

# Function to load user_info from a JSON file
def load_user_info():
    try:
        with open("users/users_info.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Function to save user_info to a JSON file
def save_user_info(user_info):
    with open("users/users_info.json", "w") as f:
        json.dump(user_info, f, indent=4)

# Load user_info as a global variable
user_info = load_user_info()
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
    global user_info
    username = st.text_input("Username", key="username")
    password = st.text_input("Password", key="password", type="password")
    if st.button("Log in"):
        user_info = load_user_info()  # Reload the user info
        user = next((user for user in user_info if user['username'] == username and user['password'] == password), None)
        if user:
            st.session_state.logged_in = True
            global learning_page
            st.switch_page(learning_page)
        else:
            st.warning('Wrong username or password!')

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
    global user_info
    new_username = st.text_input("Username", key="new_username")
    new_password = st.text_input("Password", key="new_password", type="password")
    new_email = st.text_input("Email Address", key="new_email")
    if any(user['username'] == new_username for user in user_info):
        st.warning("Username already exists!")
    elif st.button("Register"):
        # Get the last ID and increment it by 1
        new_id = max((user['id'] for user in user_info), default=0) + 1
        # Append the new user data to the user_info list
        new_user = {"id": new_id, "username": new_username, "password": new_password, "email": new_email}
        user_info.append(new_user)
        # Save the updated user_info to the JSON file
        save_user_info(user_info)
        st.success('User registered successfully!')
        user_info = load_user_info()  # Reload the user info to include the new user
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

if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Account": [logout_page],
            "Learn": [learning_page]
        }
    )
else:
    pg = st.navigation(
        {
            "Account": [login_page, register_page]
        }
    )
st.sidebar.header("Welcome to Echo English Learning System!")
pg.run()