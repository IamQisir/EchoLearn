# components/learning_form.py

import streamlit as st

class LearningForm:
    """Handles the learning form submission and processing"""
    
    def __init__(self, grid, audio_handler):
        self.grid = grid
        self.audio_handler = audio_handler
        self.audio_file = None

    def process_submission(self):
        """Process form submission and return success status"""
        with self.grid.form(key='learning_phase'):
            self.audio_file = self.audio_handler.record_audio()
            return st.form_submit_button('学習開始！')

    def get_results(self):
        """Get pronunciation assessment results"""
        if not self.audio_file:
            return None
        return self.audio_handler.process_audio(self.audio_file)

# components/summary_tab.py

class SummaryTab:
    """Handles the summary tab display and interactions"""
    
    def __init__(self, app_state, score_visualizer):
        self.app_state = app_state
        self.score_visualizer = score_visualizer

    def display(self):
        """Display summary content"""
        self.display_progress_charts()
        self.display_error_charts()

    def display_progress_charts(self):
        """Display progress charts"""
        progress_data = self.app_state.get_scores_for_lesson()
        if progress_data is not None:
            charts = self.score_visualizer.create_progress_charts(progress_data)
            st.altair_chart(charts, use_container_width=True)

    def display_error_charts(self):
        """Display error distribution charts"""
        current_errors = self.app_state.get_error_stats()
        total_errors = self.app_state.get_total_error_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            if current_errors:
                chart = self.score_visualizer.create_error_chart(
                    current_errors, '今回の発音エラー'
                )
                st.altair_chart(chart, use_container_width=True)
        
        with col2:
            if total_errors:
                chart = self.score_visualizer.create_error_chart(
                    total_errors, 'レッスン総合エラー'
                )
                st.altair_chart(chart, use_container_width=True)

# components/ai_feedback.py

class AIFeedbackComponent:
    """Handles AI feedback display and interactions"""
    
    def display(self, app_state):
        """Display AI feedback"""
        with st.chat_message('AI'):
            if not app_state.current_errors:
                st.write("練習を始めましょう！")
            elif app_state.learning_data.overall_score:
                st.write("GPTによる発音のアドバイス:")
                feedback = self.get_feedback(app_state.current_errors)
                if feedback:
                    st.write(feedback)
            else:
                st.write("まだ頑張りましょう！")

    def get_feedback(self, errors):
        """Get AI feedback for pronunciation errors"""
        from services.ai_chat import AIChat
        ai_chat = AIChat()
        return ai_chat.get_chat_response(errors)