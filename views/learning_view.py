# pages/learning_page.py

# Standard library imports
from typing import Optional, Tuple, Any
from pathlib import Path

# Third-party imports
import streamlit as st
from streamlit_extras.grid import grid as extras_grid
from streamlit_extras.let_it_rain import rain

# Local application imports
from app_state import AppState
from models.dataset import Dataset
from models.user import User
from utils.visualization import (
    create_radar_chart,
    create_waveform_plot,
    create_syllable_table,
    create_doughnut_chart,
    create_score_progress_charts
)
from utils.audio_handler import AudioHandler
from utils.ui_components import (
    create_grid_layout,
    display_lesson_content,
    display_learning_results
)
from components.learning_form import LearningForm
from components.summary_tab import SummaryTab
from components.ai_feedback import AIFeedbackComponent
from utils.state_manager import initialize_state

class LearningPage:
    """Main learning page controller"""
    
    def __init__(self):
        """Initialize learning page components"""
        self.app_state = initialize_state()
        if not self.app_state.user:
            st.warning("ログインしていません！")
            return
            
        self.audio_handler = AudioHandler(self.app_state.user)
        self.init_dataset()
        self.ai_feedback = AIFeedbackComponent(self.app_state)

    def init_dataset(self) -> None:
        """Initialize dataset for current user"""
        if 'dataset' not in st.session_state:
            dataset = Dataset(self.app_state.user.name)
            dataset.load_data()
            st.session_state.dataset = dataset
        self.dataset = st.session_state.dataset

    def setup_page(self) -> Tuple[Any, Any]:
        """Setup initial page configuration"""
        st.title("エコー英語学習システム😆")
        return st.tabs(['ラーニング', 'まとめ'])

    def handle_course_navigation(self, grid) -> str:
        """Handle course navigation and return current selection"""
        lessons = [f'レッソン{i+1}' for i in range(self.dataset.get_lesson_count())]
        selection = course_navigation(grid, lessons, self.app_state)
        return selection

    def handle_learning_submission(self, audio_file: str, text_content: str, selection: str) -> None:
        """Process learning submission"""
        try:
            pronunciation_result = self.audio_handler.process_audio(
                audio_file, text_content
            )
            
            # Save results
            self.app_state.user.save_practice_result(selection, pronunciation_result)
            
            # Update learning data
            learning_data = self.app_state.get_learning_data()
            learning_data.overall_score = pronunciation_result["NBest"][0]["PronunciationAssessment"]
            
            # Generate visualizations
            learning_data.radar_chart = create_radar_chart(pronunciation_result)
            learning_data.waveform_plot = create_waveform_plot(audio_file, pronunciation_result)
            learning_data.syllable_table = create_syllable_table(pronunciation_result)
            
            # Store results
            self.app_state.store_pronunciation_result(pronunciation_result)
            self.app_state.update_learning_data(learning_data)
            
            # Check score for celebration
            if learning_data.overall_score['PronScore'] >= 90:
                rain(
                    emoji="🥳🎉",
                    font_size=54,
                    falling_speed=5,
                    animation_length=1
                )
                
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

    def handle_learning_tab(self, tab) -> None:
        """Handle learning tab content"""
        grid = create_grid_layout()
        
        # Course navigation and content display
        selection = self.handle_course_navigation(grid)
        lesson = self.dataset.get_lesson(int(selection.replace("レッソン", "")) - 1)
        display_lesson_content(grid, lesson)
        
        # Learning form
        audio_file = None
        with grid.form(key='learning_phase'):
            audio_file = self.audio_handler.record_audio()
            if_started = st.form_submit_button('学習開始！')
            
        if if_started and audio_file:
            with open(lesson.text_path, "r", encoding='utf-8') as f:
                text_content = f.read()
            self.handle_learning_submission(audio_file, text_content, selection)
            
        # Display results
        display_learning_results(grid, self.app_state.get_learning_data())

    def handle_summary_tab(self, tab) -> None:
        """Handle summary tab content"""
        # Create and display summary tab
        summary_tab = SummaryTab(self.app_state)
        summary_tab.display()

    def run(self) -> None:
        """Main entry point for the learning page"""
        if not self.app_state.user:
            return
            
        learning_tab, summary_tab = self.setup_page()
        
        with learning_tab:
            self.handle_learning_tab(learning_tab)
            
        with summary_tab:
            self.handle_summary_tab(summary_tab)

def course_navigation(grid, lessons: list, app_state: AppState) -> str:
    """Handle course navigation
    
    Args:
        grid: Grid layout object
        lessons: List of lesson names
        app_state: Application state instance
        
    Returns:
        Current selected course name
    """
    # Previous button
    if grid.button(
        "◀ 前", 
        disabled=app_state.lesson_index == 0, 
        use_container_width=True
    ):
        app_state.lesson_index -= 1
        st.rerun()
            
    # Next button
    if grid.button(
        "次 ▶", 
        disabled=app_state.lesson_index == len(lessons) - 1, 
        use_container_width=True
    ):
        app_state.lesson_index += 1
        st.rerun()
            
    # Show current course name
    current_course = lessons[app_state.lesson_index]
    grid.info(f"現在: {current_course}")
        
    return current_course

def validate_user_login() -> bool:
    """Validate user login status
    
    Returns:
        True if user is logged in, False otherwise
    """
    if 'user' not in st.session_state:
        st.warning("ログインしていません。")
        return False
    return True

def main():
    """Main function for the learning page"""
    if not validate_user_login():
        return
        
    learning_page = LearningPage()
    learning_page.run()

if __name__ == "__main__":
    main()