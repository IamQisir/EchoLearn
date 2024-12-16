# utils/ui_components.py

import streamlit as st
from streamlit_extras.grid import grid as extras_grid

def create_grid_layout():
    """Create and return grid layout"""
    return extras_grid(
        [0.1, 0.1, 0.8], 
        [0.2, 0.8], 
        1, 
        1, 
        [0.3, 0.7], 
        1, 
        1, 
        vertical_align="center"
    )

def display_lesson_content(grid, lesson):
    """Display lesson video and text content"""
    grid.video(lesson.video_path)
    with open(lesson.text_path, "r", encoding='utf-8') as f:
        text_content = f.read()
    grid.markdown(
        f"""
        <div style="text-align: left; font-size: 24px; font-weight: bold; color: #F0F0F0;">
            {text_content}
        </div>
        """,
        unsafe_allow_html=True
    )

def display_learning_results(grid, learning_data):
    """Display learning results in the grid"""
    if learning_data.waveform_plot:
        grid.pyplot(learning_data.waveform_plot)
        
    if learning_data.radar_chart:
        grid.pyplot(learning_data.radar_chart)
        
    if learning_data.error_table is not None:
        grid.dataframe(learning_data.error_table, use_container_width=True)
        
    if learning_data.syllable_table:
        grid.markdown(learning_data.syllable_table, unsafe_allow_html=True)