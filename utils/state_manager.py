# utils/state_manager.py

import streamlit as st
from typing import Optional, TypeVar, Type, Generic, Union, Dict, Any
from dataclasses import dataclass, field
from app_state import AppState, LearningData, ScoresHistory, ErrorData
from models.user import User

T = TypeVar('T')

@dataclass
class StateContainer(Generic[T]):
    """Generic container for managing state data"""
    data: T
    initialized: bool = False
    version: int = 1

class StateManager:
    """Manages application state initialization and updates"""
    
    def __init__(self):
        """Initialize state manager"""
        self._verify_session_state()
    
    def _verify_session_state(self) -> None:
        """Verify and initialize session state if needed"""
        if 'state_manager' not in st.session_state:
            st.session_state.state_manager = {
                'app_state': StateContainer(AppState()),
                'learning_data': StateContainer(LearningData()),
                'scores_history': StateContainer({}),
                'current_errors': StateContainer({}),
                'total_errors': StateContainer({})
            }
    
    def get_app_state(self) -> AppState:
        """Get current application state.
        
        Returns:
            Current AppState instance
        """
        container = st.session_state.state_manager['app_state']
        if not container.initialized:
            self._initialize_app_state(container)
        return container.data
    
    def _initialize_app_state(self, container: StateContainer[AppState]) -> None:
        """Initialize application state with default values.
        
        Args:
            container: State container to initialize
        """
        container.initialized = True
        app_state = container.data
        
        # Initialize state if not already done
        if not hasattr(app_state, '_state'):
            app_state._state = {
                'logged_in': False,
                'user': None,
                'lesson_index': 0,
                'learning_data': LearningData(),
                'scores_history': {},
                'current_errors': {},
                'total_errors': {},
                'ai_initial_input': None
            }
    
    def update_user(self, user: User) -> None:
        """Update current user and related state.
        
        Args:
            user: User instance to set as current user
        """
        app_state = self.get_app_state()
        app_state.set_user(user)
        self._load_user_state(user)
    
    def _load_user_state(self, user: User) -> None:
        """Load state data for specified user.
        
        Args:
            user: User to load state for
        """
        app_state = self.get_app_state()
        app_state.load_state(app_state.lesson_index)
    
    def clear_state(self) -> None:
        """Clear all application state"""
        app_state = self.get_app_state()
        app_state.clear_state()
        
        # Reset all containers
        for container in st.session_state.state_manager.values():
            container.initialized = False
    
    def get_state_value(self, key: str) -> Optional[Any]:
        """Get value from application state.
        
        Args:
            key: State key to retrieve
            
        Returns:
            State value if exists, None otherwise
        """
        app_state = self.get_app_state()
        return app_state._state.get(key)
    
    def set_state_value(self, key: str, value: Any) -> None:
        """Set value in application state.
        
        Args:
            key: State key to set
            value: Value to set
        """
        app_state = self.get_app_state()
        app_state._state[key] = value
    
    def update_learning_data(self, data: Dict[str, Any]) -> None:
        """Update learning data in state.
        
        Args:
            data: New learning data to update
        """
        app_state = self.get_app_state()
        learning_data = LearningData()
        
        # Update learning data fields
        for key, value in data.items():
            if hasattr(learning_data, key):
                setattr(learning_data, key, value)
        
        app_state.update_learning_data(learning_data)
    
    def update_errors(self, current_errors: Dict[str, ErrorData],
                     lesson_index: Optional[int] = None) -> None:
        """Update error data in state.
        
        Args:
            current_errors: Current error data to update
            lesson_index: Optional lesson index for total errors
        """
        app_state = self.get_app_state()
        app_state._state['current_errors'] = current_errors
        
        if lesson_index is not None:
            if lesson_index not in app_state._state['total_errors']:
                app_state._state['total_errors'][lesson_index] = {}
            
            for error_type, data in current_errors.items():
                if error_type not in app_state._state['total_errors'][lesson_index]:
                    app_state._state['total_errors'][lesson_index][error_type] = ErrorData()
                
                total = app_state._state['total_errors'][lesson_index][error_type]
                total.count += data.count
                total.words.extend(data.words)

def initialize_state() -> AppState:
    """Initialize and return application state.
    
    Returns:
        Initialized AppState instance
    """
    state_manager = StateManager()
    return state_manager.get_app_state()

def get_current_state() -> Optional[AppState]:
    """Get current application state if initialized.
    
    Returns:
        Current AppState instance or None if not initialized
    """
    if 'state_manager' in st.session_state:
        return st.session_state.state_manager['app_state'].data
    return None

def clear_current_state() -> None:
    """Clear current application state"""
    if 'state_manager' in st.session_state:
        state_manager = StateManager()
        state_manager.clear_state()