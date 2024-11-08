import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from collections import defaultdict

def get_sorted_json_files(folder_path):
    """Get all JSON files in the folder, return their names sorted in ascending order."""
    try:
        files = os.listdir(folder_path)
        json_files = [file for file in files if file.endswith('.json')]
        json_files.sort()
        return json_files
    except Exception as e:
        st.error(f"Error reading directory: {str(e)}")
        return []

def load_json_files(folder_path, json_files):
    """Load all JSON files and return their content."""
    json_contents = []
    for file_name in json_files:
        try:
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                json_contents.append(content)
        except Exception as e:
            st.warning(f"Error loading {file_name}: {str(e)}")
    return json_contents

def analyze_pronunciation_errors(json_contents):
    """Analyze pronunciation errors from all JSON files."""
    error_counts = defaultdict(int)
    total_words = 0
    
    for content in json_contents:
        try:
            words = content['NBest'][0]['Words']
            total_words += len(words)
            
            for word in words:
                if 'PronunciationAssessment' in word:
                    error_type = word['PronunciationAssessment'].get('ErrorType', 'None')
                    if error_type != 'None':
                        error_counts[error_type] += 1
        except Exception as e:
            st.warning(f"Error analyzing content: {str(e)}")
    
    return dict(error_counts), total_words

def create_error_pie_chart(error_counts, total_words):
    """Create a pie chart showing error distribution."""
    if not error_counts:
        st.warning("No errors found in the data.")
        return
    
    # Calculate percentages
    error_percentages = {k: (v/total_words)*100 for k, v in error_counts.items()}
    
    # Create pie chart
    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(
        error_percentages.values(),
        labels=error_percentages.keys(),
        autopct='%1.1f%%',
        textprops={'fontsize': 12}
    )
    
    # Add title
    plt.title("Pronunciation Mistakes Ratio", pad=20, fontsize=14)
    
    return fig

def show_pronunciation_analysis(folder_path):
    """Main function to show pronunciation analysis."""
    st.title("発音分析レポート")
    
    # Get and load JSON files
    json_files = get_sorted_json_files(folder_path)
    if not json_files:
        st.error("JSONファイルが見つかりません。")
        return
    
    json_contents = load_json_files(folder_path, json_files)
    if not json_contents:
        st.error("JSONファイルを読み込めません。")
        return
    
    # Analyze errors
    error_counts, total_words = analyze_pronunciation_errors(json_contents)
    
    # Show statistics
    st.write("### 基本統計")
    st.write(f"- 分析した単語数: {total_words}")
    st.write(f"- 検出されたエラーの種類: {len(error_counts)}")
    
    # Show error distribution
    st.write("### エラー分布")
    if error_counts:
        fig = create_error_pie_chart(error_counts, total_words)
        st.pyplot(fig)
    
    # Show detailed error counts
    st.write("### エラー詳細")
    error_df = pd.DataFrame(
        [(k, v, f"{(v/total_words)*100:.1f}%") for k, v in error_counts.items()],
        columns=["エラータイプ", "回数", "割合"]
    )
    st.dataframe(error_df)

# Example usage
if __name__ == "__main__":
    folder_path = r"E:\Code\EchoLearn\database\qi\practice_history\2024-10-31"
    show_pronunciation_analysis(folder_path)