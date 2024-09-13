import gradio as gr
import matplotlib.pyplot as plt
import numpy as np

def plot_function():
    # 创建一个示例图像
    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x)

    fig, ax = plt.subplots()
    ax.plot(x, y)
    
    return fig

# 使用 gr.Plot 组件直接显示 Matplotlib 图像
demo = gr.Interface(fn=plot_function, inputs=[], outputs=gr.Plot())

demo.launch()