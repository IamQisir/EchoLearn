import json
import os
import streamlit as st
import bcrypt
from datetime import datetime
from datetime import date

class User:
    user_info_path = "database/all_users/users_info.json"
    info_folder = "database/all_users/"
    user_info = {}

    # load user_info from json file
    with open(user_info_path, "r") as f:
        user_info = json.load(f)
    
    def __init__(self, name:str, password:str) -> None:
        self.name = name
        # hash the password to ensure the cybersecurity
        self.password = User.hash_password(password)
        self.user_path = f"database/{name}/"
        # every practice history will be stored 
        self.practice_history_path = self.user_path + "practice_history/"
        # in order to save voice files within, to check and create folders in advance
        if not os.path.exists(self.practice_history_path):
            os.makedirs(self.practice_history_path, exist_ok=False)
        self.today_path = self.practice_history_path + f"{str(date.today())}/"
        if not os.path.exists(self.today_path):
            os.makedirs(self.today_path, exist_ok=False)
    
    def __hash__(self):
        return hash(self.name)

    def save_to_user_info(self) -> None:
        # update the user_info like registering a new user
        User.user_info[self.name] = {
            "password": self.password,
            "history": []
        }
        with open(User.user_info_path, 'w') as f:
            json.dump(User.user_info, f, indent=4)

    def save_pron_history(self, selection:str, pronunciation_result:str):
        # save all the user's practice history
        # if the folder already exists, don't rewrite it 
        # create the history folder of today within the folder of self.practice_history
        print(self.today_path)
        result_file_path = f"{self.today_path}{selection}-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        print(result_file_path)
        with open(result_file_path, 'w') as f:
            json.dump(pronunciation_result, f, indent=4)
    
    @classmethod
    def register(cls, name:str, password:str):
        # check if the user already existed 
        if name in cls.user_info:
            st.warning("ユーザーは既に存在しています!")
            return None
        # create directories of new user (big directory)
        new_user = cls(name, password)
        try:
            os.makedirs(new_user.user_path, exist_ok=False)
        except FileExistsError:
            st.warning("ユーザーは既に存在しています！")
        except Exception as e:
            st.warning("エラーが生じました！係員に連絡してください！")
            print(f"An error occurred while creating the directory: {e}")
        new_user.save_to_user_info()
        return new_user
    
    def load_scores_history(self, lesson_index: int):
        scores_dir = os.path.join(self.today_path, "scores")
        json_file = os.path.join(scores_dir, "lesson_scores.json")
        
        # Initialize or reset scores history for current lesson
        if 'scores_history' not in st.session_state:
            st.session_state.scores_history = {}
        
        # Load saved scores if file exists
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                all_scores = json.load(f)
                lesson_key = f"lesson_{lesson_index}"
                
                if lesson_key in all_scores:
                    st.session_state.scores_history[lesson_index] = all_scores[lesson_key]
                else:
                    st.session_state.scores_history[lesson_index] = {
                        'AccuracyScore': [],
                        'FluencyScore': [],
                        'CompletenessScore': [],
                        'PronScore': []
                    }
        else:
            st.session_state.scores_history[lesson_index] = {
                'AccuracyScore': [],
                'FluencyScore': [],
                'CompletenessScore': [],
                'PronScore': []
            }
            
    def load_errors_history(self, lesson_index: int):
        """Load error history for specified lesson"""
        scores_dir = os.path.join(self.today_path, "scores")
        error_file = os.path.join(scores_dir, "error_history.json")
        
        # Initialize error history if not exists
        if 'error_history' not in st.session_state:
            st.session_state.error_history = {
                'current_errors': {},
                'total_errors': {}
            }
        
        # Load saved errors if file exists
        if os.path.exists(error_file):
            with open(error_file, 'r', encoding='utf-8') as f:
                all_errors = json.load(f)
                lesson_key = f"lesson_{lesson_index}"
                
                if lesson_key in all_errors:
                    st.session_state.error_history['current_errors'] = all_errors[lesson_key]['current']
                    st.session_state.error_history['total_errors'][lesson_index] = all_errors[lesson_key]['total']
                else:
                    st.session_state.error_history['current_errors'] = {}
                    st.session_state.error_history['total_errors'][lesson_index] = {}

    @classmethod
    def login(cls, name:str, password:str):
        if name in User.user_info:
            if User.check_password(User.user_info['qi']['password'], password):
                # user's folder has been already created when in registration
                return cls(name, password)
        st.warning('入力されたパスワードが間違っています！')
        
    @staticmethod
    def hash_password(password, rounds=12):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds)).decode()
    
    @staticmethod
    def check_password(hashed_password, user_password):
        return bcrypt.checkpw(user_password.encode(), hashed_password.encode())
    

