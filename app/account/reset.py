import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import time

# Load user configuration
yaml_path = "users/config.yaml"

with open(yaml_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

def show_forgot_password_page():
    st.header("Reset Password")
    with st.form("reset_password_form"):
        username = st.text_input("Username")
        new_password = st.text_input("New Password", type="password")
        new_password_repeat = st.text_input("Repeat New Password", type="password")

        if st.form_submit_button("Reset Password"):
            if new_password == new_password_repeat:
                if username in config['credentials']['usernames']:
                    # Hash the new password
                    hashed_password = stauth.Hasher([new_password]).generate()[0]
                    
                    # Update user's password in config
                    config['credentials']['usernames'][username]['password'] = hashed_password
                    
                    # Save updated config
                    with open(yaml_path, 'w') as file:
                        yaml.dump(config, file, default_flow_style=False)
                    
                    st.success("Password reset successfully. Please log in with your new password.")
                    time.sleep(1)
                    st.query_params.page = "login"
                else:
                    st.error("Username not found")
            else:
                st.error("Passwords do not match")

if __name__ == "__main__":
    show_forgot_password_page()