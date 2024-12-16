# app_state.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import streamlit as st
import json
import os
from datetime import datetime
from models.user import User
import pandas as pd

@dataclass
class LearningData:
    overall_score: Optional[Dict] = None
    radar_chart: Optional[Any] = None
    waveform_plot: Optional[Any] = None
    error_table: Optional[Any] = None
    syllable_table: Optional[Any] = None

@dataclass
class ScoresHistory:
    accuracy_scores: List[float] = field(default_factory=list)
    fluency_scores: List[float] = field(default_factory=list)
    completeness_scores: List[float] = field(default_factory=list)
    prosody_scores: List[float] = field(default_factory=list)
    pron_scores: List[float] = field(default_factory=list)

@dataclass
class ErrorData:
    count: int = 0
    words: List[str] = field(default_factory=list)

class AppState:
    """Manages application state and persistence"""
    
    def __init__(self):
        self._initialize_state()
        
    def _initialize_state(self):
        """Initialize or load state from session"""
        if not hasattr(self, '_state'):
            self._state = {
                'logged_in': False,
                'user': None,
                'lesson_index': 0,
                'learning_data': LearningData(),
                'scores_history': {},
                'current_errors': {},
                'total_errors': {},
                'ai_initial_input': None
            }
    
    @property
    def logged_in(self) -> bool:
        return self._state['logged_in']
    
    @logged_in.setter
    def logged_in(self, value: bool):
        self._state['logged_in'] = value
    
    @property
    def user(self) -> Optional[User]:
        return self._state['user']
    
    def set_user(self, user: User):
        """Set current user and initialize user-specific state"""
        self._state['user'] = user
        self.logged_in = True
        self._initialize_user_state()
    
    def _initialize_user_state(self):
        """Initialize user-specific state and load saved data"""
        if self.user:
            self.load_state(self.lesson_index)
    
    @property
    def lesson_index(self) -> int:
        return self._state['lesson_index']
    
    @lesson_index.setter
    def lesson_index(self, value: int):
        self._state['lesson_index'] = value
        if self.user:
            self.load_state(value)
    
    @property
    def current_errors(self) -> Dict[str, ErrorData]:
        return self._state['current_errors']
    
    @property
    def total_errors(self) -> Dict[int, Dict[str, ErrorData]]:
        return self._state['total_errors']
    
    @property
    def scores_history(self) -> Dict[int, ScoresHistory]:
        return self._state['scores_history']
    
    def get_learning_data(self) -> LearningData:
        return self._state['learning_data']
    
    def update_learning_data(self, data: LearningData):
        self._state['learning_data'] = data
    
    def store_pronunciation_result(self, pronunciation_result: dict, lesson_index: int):
        """Store pronunciation results and update state"""
        scores = pronunciation_result["NBest"][0]["PronunciationAssessment"]
        error_data = self._collect_errors(pronunciation_result)
        
        # Update scores history
        if lesson_index not in self._state['scores_history']:
            self._state['scores_history'][lesson_index] = ScoresHistory()
            
        current_scores = self._state['scores_history'][lesson_index]
        current_scores.accuracy_scores.append(scores['AccuracyScore'])
        current_scores.fluency_scores.append(scores['FluencyScore'])
        current_scores.completeness_scores.append(scores['CompletenessScore'])
        current_scores.prosody_scores.append(scores['ProsodyScore'])
        current_scores.pron_scores.append(scores['PronScore'])
        
        # Update errors
        self._state['current_errors'] = error_data
        self._update_total_errors(error_data, lesson_index)
        
        # Save to files
        self._save_scores_to_file(lesson_index)
        self._save_errors_to_file(lesson_index)
    
    def _collect_errors(self, pronunciation_result: dict) -> Dict[str, ErrorData]:
        """Collect error statistics from pronunciation result"""
        error_types = {
            "省略 (Omission)": ErrorData(),
            "挿入 (Insertion)": ErrorData(),
            "発音ミス (Mispronunciation)": ErrorData(),
            "不適切な間 (UnexpectedBreak)": ErrorData(),
            "間の欠如 (MissingBreak)": ErrorData(),
            "単調 (Monotone)": ErrorData()
        }
        
        error_mapping = {
            "Omission": "省略 (Omission)",
            "Insertion": "挿入 (Insertion)",
            "Mispronunciation": "発音ミス (Mispronunciation)",
            "UnexpectedBreak": "不適切な間 (UnexpectedBreak)",
            "MissingBreak": "間の欠如 (MissingBreak)",
            "Monotone": "単調 (Monotone)"
        }
        
        words = pronunciation_result["NBest"][0]["Words"]
        for word in words:
            if ("PronunciationAssessment" in word and 
                "ErrorType" in word["PronunciationAssessment"]):
                error_type = word["PronunciationAssessment"]["ErrorType"]
                if error_type and error_type in error_mapping:
                    jp_error = error_mapping[error_type]
                    error_types[jp_error].count += 1
                    error_types[jp_error].words.append(word["Word"])
                    
        return error_types
    
    def _update_total_errors(self, current_errors: Dict[str, ErrorData], lesson_index: int):
        """Update total error counts for the lesson"""
        if lesson_index not in self._state['total_errors']:
            self._state['total_errors'][lesson_index] = {}
            
        for error_type, data in current_errors.items():
            if error_type not in self._state['total_errors'][lesson_index]:
                self._state['total_errors'][lesson_index][error_type] = ErrorData()
                
            total = self._state['total_errors'][lesson_index][error_type]
            total.count += data.count
            total.words.extend(data.words)
    
    def _save_scores_to_file(self, lesson_index: int):
        """Save scores history to JSON file"""
        if not self.user:
            return
            
        scores_dir = os.path.join(self.user.today_path, "scores")
        os.makedirs(scores_dir, exist_ok=True)
        
        scores_file = os.path.join(scores_dir, "lesson_scores.json")
        current_scores = self._state['scores_history'][lesson_index]
        
        scores_data = {
            f"lesson_{lesson_index}": {
                "AccuracyScore": current_scores.accuracy_scores,
                "FluencyScore": current_scores.fluency_scores,
                "CompletenessScore": current_scores.completeness_scores,
                "ProsodyScore": current_scores.prosody_scores,
                "PronScore": current_scores.pron_scores
            }
        }
        
        with open(scores_file, 'w', encoding='utf-8') as f:
            json.dump(scores_data, f, indent=4)
    
    def _save_errors_to_file(self, lesson_index: int):
        """Save error history to JSON file"""
        if not self.user:
            return
            
        scores_dir = os.path.join(self.user.today_path, "scores")
        os.makedirs(scores_dir, exist_ok=True)
        
        error_file = os.path.join(scores_dir, "error_history.json")
        
        error_data = {
            f"lesson_{lesson_index}": {
                "current": self._state['current_errors'],
                "total": self._state['total_errors'][lesson_index]
            }
        }
        
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=4, ensure_ascii=False)
    
    def load_state(self, lesson_index: int):
        """Load saved state from files"""
        if not self.user:
            return
            
        self._load_scores(lesson_index)
        self._load_errors(lesson_index)
    
    def _load_scores(self, lesson_index: int):
        """Load scores history from file"""
        scores_file = os.path.join(self.user.today_path, "scores", "lesson_scores.json")
        
        if os.path.exists(scores_file):
            with open(scores_file, 'r', encoding='utf-8') as f:
                scores_data = json.load(f)
                lesson_key = f"lesson_{lesson_index}"
                
                if lesson_key in scores_data:
                    self._state['scores_history'][lesson_index] = ScoresHistory(
                        accuracy_scores=scores_data[lesson_key]["AccuracyScore"],
                        fluency_scores=scores_data[lesson_key]["FluencyScore"],
                        completeness_scores=scores_data[lesson_key]["CompletenessScore"],
                        prosody_scores=scores_data[lesson_key]["ProsodyScore"],
                        pron_scores=scores_data[lesson_key]["PronScore"]
                    )
    
    def _load_errors(self, lesson_index: int):
        """Load error history from file"""
        error_file = os.path.join(self.user.today_path, "scores", "error_history.json")
        
        if os.path.exists(error_file):
            with open(error_file, 'r', encoding='utf-8') as f:
                error_data = json.load(f)
                lesson_key = f"lesson_{lesson_index}"
                
                if lesson_key in error_data:
                    self._state['current_errors'] = error_data[lesson_key]['current']
                    self._state['total_errors'][lesson_index] = error_data[lesson_key]['total']
    
    def clear_state(self):
        """Clear application state"""
        self._state = {
            'logged_in': False,
            'user': None,
            'lesson_index': 0,
            'learning_data': LearningData(),
            'scores_history': {},
            'current_errors': {},
            'total_errors': {},
            'ai_initial_input': None
        }

    def get_error_stats(self) -> Dict[str, int]:
        """Get current error statistics"""
        return {k: v.count for k, v in self._state['current_errors'].items() if v.count > 0}

    def get_total_error_stats(self) -> Dict[str, int]:
        """Get total error statistics for current lesson"""
        if self.lesson_index not in self._state['total_errors']:
            return {}
        return {k: v.count for k, v in self._state['total_errors'][self.lesson_index].items() if v.count > 0}

    def get_scores_for_lesson(self, lesson_index: int) -> Optional[pd.DataFrame]:
        """Get scores history for specific lesson as DataFrame"""
        if lesson_index not in self._state['scores_history']:
            return None
            
        scores = self._state['scores_history'][lesson_index]
        if not any([scores.accuracy_scores, scores.fluency_scores,
                   scores.completeness_scores, scores.prosody_scores,
                   scores.pron_scores]):
            return None
            
        return pd.DataFrame({
            'Attempt': range(1, len(scores.pron_scores) + 1),
            'PronScore': scores.pron_scores,
            'AccuracyScore': scores.accuracy_scores,
            'FluencyScore': scores.fluency_scores,
            'CompletenessScore': scores.completeness_scores,
            'ProsodyScore': scores.prosody_scores
        })