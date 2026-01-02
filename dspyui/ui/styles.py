"""
CSS 样式定义

INPUT:  无
OUTPUT: CUSTOM_CSS 常量
POS:    UI 样式模块，被 app.py 引用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

# Gradio 自定义 CSS 样式
CUSTOM_CSS: str = """
.expand-button {
  min-width: 20px !important;
  width: 20px !important;
  padding: 0 !important;
  font-size: 10px !important;
}
.prompt-card {
  height: 150px !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: space-between !important;
  padding: 10px !important;
  position: relative !important;
}
.prompt-details {
  flex-grow: 1 !important;
}
.view-details-btn {
  position: absolute !important;
  bottom: 10px !important;
  right: 10px !important;
}
.red-text {
  color: red !important;
}
.language-notice {
  background-color: #fff3cd !important;
  border: 1px solid #ffeaa7 !important;
  border-radius: 4px !important;
  padding: 10px !important;
  margin: 10px 0 !important;
  color: #856404 !important;
}
/* 优化提示词文本框滚动样式 */
.optimized-prompt-textbox textarea {
  max-height: 400px !important;
  overflow-y: auto !important;
}
"""
