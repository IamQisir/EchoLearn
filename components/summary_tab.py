# components/summary_tab.py

import streamlit as st
import pandas as pd
from typing import Optional

from app_state import AppState
from utils.visualization import (
    create_score_progress_charts,
    create_doughnut_chart,
)
from services.ai_chat import AIChat

class SummaryTab:
    """Component for displaying learning summary and analysis"""
    
    def __init__(self, app_state: AppState):
        """Initialize SummaryTab component.
        
        Args:
            app_state: Application state instance
        """
        self.app_state = app_state
        self.ai_chat = AIChat()
        
    def display_progress_section(self) -> None:
        """Display learning progress charts"""
        st.subheader("学習進捗 📈")
        
        scores_data = self.app_state.get_scores_for_lesson(
            self.app_state.lesson_index
        )
        
        if scores_data is not None and not scores_data.empty:
            progress_charts = create_score_progress_charts(scores_data)
            st.altair_chart(progress_charts, use_container_width=True)
        else:
            st.info("まだ学習記録がありません。")
    
    def display_error_analysis(self) -> None:
        """Display error analysis charts"""
        st.subheader("発音エラー分析 🎯")
        
        col1, col2 = st.columns(2)
        
        # Current session errors
        with col1:
            st.markdown("### 今回の発音エラー")
            current_errors = self.app_state.get_error_stats()
            if current_errors:
                chart = create_doughnut_chart(
                    current_errors, 
                    '今回の発音エラー分布'
                )
                st.altair_chart(chart, use_container_width=True)
                
                # Display detailed error list
                st.markdown("#### エラー詳細")
                for error_type, count in current_errors.items():
                    st.markdown(f"- {error_type}: {count}回")
            else:
                st.info("現在のセッションにエラーはありません。")
        
        # Total lesson errors
        with col2:
            st.markdown("### レッスン総合エラー")
            total_errors = self.app_state.get_total_error_stats()
            if total_errors:
                chart = create_doughnut_chart(
                    total_errors, 
                    'レッスン総合エラー分布'
                )
                st.altair_chart(chart, use_container_width=True)
                
                # Display detailed error list
                st.markdown("#### エラー詳細")
                for error_type, count in total_errors.items():
                    st.markdown(f"- {error_type}: {count}回")
            else:
                st.info("このレッスンにはまだエラー記録がありません。")
    
    def display_ai_feedback(self) -> None:
        """Display AI feedback section"""
        st.subheader("AI発音フィードバック 🤖")
        
        with st.chat_message('assistant'):
            if not self.app_state.current_errors:
                st.write("練習を始めましょう！")
                return
                
            current_errors = self.app_state.current_errors
            feedback = self.ai_chat.get_chat_response(current_errors)
            
            if feedback:
                for chunk in feedback:
                    st.write(chunk)
            else:
                st.write("フィードバックを生成できませんでした。")
    
    def display_learning_statistics(self) -> None:
        """Display learning statistics"""
        st.subheader("学習統計 📊")
        
        scores_data = self.app_state.get_scores_for_lesson(
            self.app_state.lesson_index
        )
        
        if scores_data is not None and not scores_data.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_score = scores_data['PronScore'].mean()
                st.metric(
                    label="平均スコア", 
                    value=f"{avg_score:.1f}",
                    delta=f"{scores_data['PronScore'].iloc[-1] - avg_score:.1f}"
                )
                
            with col2:
                max_score = scores_data['PronScore'].max()
                st.metric(
                    label="最高スコア",
                    value=f"{max_score:.1f}"
                )
                
            with col3:
                practice_count = len(scores_data)
                st.metric(
                    label="練習回数",
                    value=str(practice_count)
                )
    
    def display(self) -> None:
        """Display complete summary tab"""
        if not self.app_state.user:
            st.warning("ログインしていません。")
            return
            
        # Learning statistics at the top
        self.display_learning_statistics()
        
        # Progress charts
        self.display_progress_section()
        
        # Error analysis
        self.display_error_analysis()
        
        # AI feedback at the bottom
        self.display_ai_feedback()

def create_summary_tab(app_state: AppState) -> SummaryTab:
    """Factory function to create SummaryTab instance"""
    return SummaryTab(app_state)