# components/ai_feedback.py

import streamlit as st
from typing import Dict, Optional, Any
from services.ai_chat import AIChat
from app_state import AppState

class AIFeedbackComponent:
    """Component for handling AI-powered pronunciation feedback"""
    
    def __init__(self, app_state: AppState):
        """Initialize AI Feedback component.
        
        Args:
            app_state: Application state instance
        """
        self.app_state = app_state
        self.ai_chat = AIChat()
        
    def _format_error_message(self, errors: Dict[str, Any]) -> str:
        """Format error data into a human-readable message.
        
        Args:
            errors: Dictionary containing error information
            
        Returns:
            Formatted error message string
        """
        messages = []
        for error_type, data in errors.items():
            if data['count'] > 0:
                word_list = ', '.join(data['words'])
                messages.append(
                    f"- {error_type}：{data['count']}回 "
                    f"(発生した単語: {word_list})"
                )
        
        if messages:
            return "発音エラーの詳細：\n" + "\n".join(messages)
        return "エラーはありません。"

    def _display_initial_state(self) -> None:
        """Display initial state when no practice has been done"""
        st.markdown("""
        ### AIフィードバック 🤖
        
        練習を始めましょう！AI先生があなたの発音を分析し、
        改善のためのアドバイスを提供します。
        
        - 発音の正確性
        - 流暢さ
        - リズムとイントネーション
        
        について詳しいフィードバックが得られます。
        """)

    def _display_processing_state(self) -> None:
        """Display processing state while generating feedback"""
        with st.status("AIフィードバックを生成中...", expanded=True) as status:
            st.write("発音エラーを分析中...")
            st.write("フィードバックを作成中...")
            status.update(label="完了！", state="complete")

    def _display_error_summary(self, errors: Dict[str, Any]) -> None:
        """Display summary of pronunciation errors.
        
        Args:
            errors: Dictionary containing error information
        """
        st.markdown("### 発音エラーサマリー 📊")
        error_message = self._format_error_message(errors)
        st.markdown(error_message)

    def _display_feedback(self, errors: Dict[str, Any]) -> None:
        """Display AI feedback for pronunciation errors.
        
        Args:
            errors: Dictionary containing error information
        """
        st.markdown("### AI先生からのアドバイス 💡")
        
        feedback_placeholder = st.empty()
        with feedback_placeholder:
            with st.chat_message('assistant'):
                feedback = self.ai_chat.get_chat_response(errors)
                if feedback:
                    message = ""
                    for chunk in feedback:
                        message += chunk
                        st.markdown(message + "▌")
                    st.markdown(message)
                else:
                    st.warning("フィードバックの生成中にエラーが発生しました。")

    def _display_practice_suggestions(self) -> None:
        """Display practice suggestions based on errors"""
        st.markdown("### 練習のポイント ✨")
        st.markdown("""
        1. 音声をゆっくり、はっきりと発音してください
        2. 各単語の間に適切な間を置いてください
        3. 文全体のリズムとイントネーションに注意してください
        """)

    def display(self) -> None:
        """Display the complete AI feedback section"""
        st.markdown("## AI発音フィードバック 🎓")
        
        if not self.app_state.current_errors:
            self._display_initial_state()
            return
        
        # Create tabs for different feedback sections
        error_tab, feedback_tab, practice_tab = st.tabs([
            "エラー分析", "AIアドバイス", "練習ポイント"
        ])
        
        with error_tab:
            self._display_error_summary(self.app_state.current_errors)
            
        with feedback_tab:
            self._display_feedback(self.app_state.current_errors)
            
        with practice_tab:
            self._display_practice_suggestions()

def create_ai_feedback_component(app_state: AppState) -> AIFeedbackComponent:
    """Factory function to create AIFeedbackComponent instance.
    
    Args:
        app_state: Application state instance
        
    Returns:
        Configured AIFeedbackComponent instance
    """
    return AIFeedbackComponent(app_state)