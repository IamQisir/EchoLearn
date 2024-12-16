# models/dataset.py

from dataclasses import dataclass
from typing import List, Optional
import os
from pathlib import Path

@dataclass
class Lesson:
    """Represents a single lesson with its content"""
    text_path: str
    video_path: str
    name: str

class Dataset:
    """Manages learning content dataset"""
    
    ROOT_PATH = Path("database/learning_database")
    
    def __init__(self, user_name: str):
        self.user_path = self.ROOT_PATH / user_name
        self.lessons: List[Lesson] = []
        
    def load_data(self) -> None:
        """Load all lesson data for the user"""
        if not self.user_path.exists():
            self._build_dirs()
            
        text_files = sorted(self.user_path.glob("*.txt"))
        video_files = sorted(self.user_path.glob("*.mp4"))
        
        if len(text_files) != len(video_files):
            raise ValueError("Number of text and video files don't match")
            
        for i, (text_file, video_file) in enumerate(zip(text_files, video_files)):
            lesson_name = f"レッソン{i+1}"
            self.lessons.append(Lesson(
                text_path=str(text_file),
                video_path=str(video_file),
                name=lesson_name
            ))
    
    def _build_dirs(self) -> None:
        """Create necessary directories"""
        try:
            self.user_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create directories: {e}")
            
    def get_lesson(self, index: int) -> Optional[Lesson]:
        """Get lesson by index"""
        if 0 <= index < len(self.lessons):
            return self.lessons[index]
        return None
    
    def get_lesson_count(self) -> int:
        """Get total number of lessons"""
        return len(self.lessons)
    
    @property
    def base_path(self) -> str:
        """Get base path for the dataset"""
        return str(self.user_path)