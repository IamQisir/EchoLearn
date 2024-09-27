import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import time

# Load user configuration
yaml_path = "users/config.yaml"

with open(yaml_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

def show_register_page():
    st.header("Create New Account")
    with st.form("signup_form"):
        new_username = st.text_input("Username")
        new_name = st.text_input("Name")
        new_password = st.text_input("Password", type="password")
        new_password_repeat = st.text_input("Repeat Password", type="password")

        if st.form_submit_button("Sign Up"):
            if new_password == new_password_repeat:
                # Hash the password
                hashed_password = stauth.Hasher([new_password]).generate()[0]
                
                # Add new user to config
                config['credentials']['usernames'][new_username] = {
                    'name': new_name,
                    'password': hashed_password
                }
                
                # Save updated config
                with open(yaml_path, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
                
                st.success("Account created successfully. Please log in.")
                time.sleep(1)
                st.query_params.page = "login"
            else:
                st.error("Passwords do not match")

if __name__ == "__main__":
    show_register_page()