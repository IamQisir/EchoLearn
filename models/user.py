# models/user.py

from dataclasses import dataclass
from datetime import date, datetime
import json
import os
from pathlib import Path
import bcrypt
import streamlit as st
from typing import Dict, Any, Optional

@dataclass
class UserCredentials:
    """User credentials information"""
    name: str
    password_hash: str

class User:
    """Manages user data and authentication"""
    
    USER_INFO_PATH = Path("database/all_users/users_info.json")
    INFO_FOLDER = Path("database/all_users")
    
    def __init__(self, credentials: UserCredentials):
        self.credentials = credentials
        self.user_path = Path(f"database/{credentials.name}")
        self.practice_history_path = self.user_path / "practice_history"
        self.today_path = self.practice_history_path / str(date.today())
        self._ensure_directories()
        
    @classmethod
    def load_user_info(cls) -> Dict[str, Any]:
        """Load user information from JSON file"""
        if not cls.USER_INFO_PATH.exists():
            cls.INFO_FOLDER.mkdir(parents=True, exist_ok=True)
            return {}
            
        with open(cls.USER_INFO_PATH, 'r') as f:
            return json.load(f)
    
    def _ensure_directories(self) -> None:
        """Ensure all necessary directories exist"""
        self.practice_history_path.mkdir(parents=True, exist_ok=True)
        self.today_path.mkdir(parents=True, exist_ok=True)
    
    def save_practice_result(self, selection: str, result: Dict[str, Any]) -> None:
        """Save practice result to file"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        result_path = self.today_path / f"{selection}-{timestamp}.json"
        
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=4)
    
    @classmethod
    def register(cls, name: str, password: str) -> Optional['User']:
        """Register a new user"""
        user_info = cls.load_user_info()
        
        if name in user_info:
            st.warning("ユーザーは既に存在しています!")
            return None
            
        try:
            credentials = UserCredentials(
                name=name,
                password_hash=cls._hash_password(password)
            )
            user = cls(credentials)
            user._save_to_user_info()
            return user
            
        except Exception as e:
            st.warning("エラーが生じました！実験実施者にご連絡してください！")
            print(f"Error during registration: {e}")
            return None
    
    @classmethod
    def login(cls, name: str, password: str) -> Optional['User']:
        """Login existing user"""
        user_info = cls.load_user_info()
        
        if name not in user_info:
            st.warning("ユーザーが存在しません！")
            return None
            
        if not cls._verify_password(user_info[name]['password'], password):
            st.warning('入力されたパスワードが間違っています！')
            return None
            
        credentials = UserCredentials(
            name=name,
            password_hash=user_info[name]['password']
        )
        return cls(credentials)
    
    def _save_to_user_info(self) -> None:
        """Save user information to JSON file"""
        user_info = self.load_user_info()
        user_info[self.credentials.name] = {
            "password": self.credentials.password_hash,
            "history": []
        }
        
        with open(self.USER_INFO_PATH, 'w') as f:
            json.dump(user_info, f, indent=4)
    
    @staticmethod
    def _hash_password(password: str, rounds: int = 12) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(
            password.encode(), 
            bcrypt.gensalt(rounds)
        ).decode()
    
    @staticmethod
    def _verify_password(stored_hash: str, provided_password: str) -> bool:
        """Verify password against stored hash"""
        return bcrypt.checkpw(
            provided_password.encode(), 
            stored_hash.encode()
        )