"""
中文翻译字典

INPUT:  无
OUTPUT: TRANSLATIONS 字典
POS:    中文翻译数据，被 i18n.__init__ 模块加载

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

TRANSLATIONS = {
    # 通用组件
    "common": {
        "language_selector": "语言",
        "chinese": "中文",
        "english": "English"
    },
    
    # 编译程序 Tab
    "compile": {
        "tab_title": "编译程序",
        "title": "DSPyUI: DSPy 的 Gradio 用户界面",
        "subtitle": "通过指定设置和提供示例数据来编译 DSPy 程序。",
        
        # 示例按钮
        "examples": {
            "title": "演示示例：",
            "judging_jokes": "评判笑话",
            "telling_jokes": "讲笑话",
            "rewriting_jokes": "改写笑话",
            "judging_jokes_instruction": "评判笑话是否有趣",
            "telling_jokes_instruction": "讲一个有趣的笑话",
            "rewriting_jokes_instruction": "用喜剧演员的风格改写",
            "joke_desc": "要评判的笑话",
            "topic_desc": "笑话的主题",
            "funny_desc": "笑话是否有趣，1 或 0。",
            "joke_output_desc": "有趣的笑话",
            "joke_input_desc": "要改写的笑话",
            "comedian_desc": "喜剧演员风格",
            "rewritten_joke_desc": "改写后的笑话"
        },
        
        # 任务指令
        "instructions": {
            "label": "任务指令",
            "placeholder": "在此输入详细的任务指令。",
            "info": "为任务提供清晰全面的指令。"
        },
        
        # 输入/输出字段
        "inputs": {
            "title": "输入",
            "description": "为您的任务添加输入字段。",
            "add_button": "添加输入字段",
            "remove_button": "移除最后输入",
            "placeholder_name": "输入{i}",
            "placeholder_desc": "描述（可选）",
            "name_info": "指定此输入字段的名称。",
            "placeholder_message": "请至少添加一个输入字段。"
        },
        
        "outputs": {
            "title": "输出",
            "description": "为您的任务添加输出字段。",
            "add_button": "添加输出字段",
            "remove_button": "移除最后输出",
            "placeholder_name": "输出{i}",
            "placeholder_desc": "描述（可选）",
            "name_info": "指定此输出字段的名称。",
            "placeholder_message": "请至少添加一个输出字段。"
        },
        
        # 数据区域
        "data": {
            "title": "数据",
            "description": "为您的任务提供示例数据。",
            "enter_manually": "手动输入",
            "upload_csv": "上传 CSV",
            "export_csv": "导出为 CSV",
            "download_csv": "下载 CSV",
            "example_data_label": "示例数据"
        },
        
        # 设置区域
        "settings": {
            "title": "设置",
            "model_label": "模型",
            "model_info": "选择主要语言模型。",
            "teacher_label": "教师模型",
            "teacher_info": "选择用于编译的教师模型。",
            "module_label": "模块",
            "module_info": "选择 DSPy 模块。",
            "hint_label": "提示",
            "hint_placeholder": "为 ChainOfThoughtWithHint 输入提示。",
            "optimizer_label": "优化器",
            "optimizer_info": "选择优化策略。",
            "metric_label": "评估指标",
            "metric_info": "选择评估指标。",
            "judge_prompt_label": "评判提示词"
        },
        
        # 模块选项
        "modules": {
            "predict": "预测",
            "chain_of_thought": "思维链",
            "chain_of_thought_with_hint": "带提示的思维链"
        },
        
        # 优化器选项
        "optimizers": {
            "bootstrap_few_shot": "少样本引导",
            "bootstrap_few_shot_with_random_search": "随机搜索少样本引导",
            "mipro": "MIPRO",
            "miprov2": "MIPROv2",
            "copro": "COPRO"
        },
        
        # 评估指标选项
        "metrics": {
            "exact_match": "精确匹配",
            "cosine_similarity": "余弦相似度",
            "llm_as_judge": "LLM 评判"
        },
        
        # 按钮
        "buttons": {
            "compile": "编译程序",
            "generate": "生成",
            "select_random_row": "选择随机行"
        },
        
        # 结果区域
        "results": {
            "title": "结果",
            "signature_label": "签名",
            "evaluation_score_label": "评估分数",
            "baseline_score_label": "基线分数",
            "optimized_prompt_label": "优化后的提示词",
            "generated_response_label": "生成的响应",
            "select_row_label": "从数据集中选择一行"
        },
        
        # 错误消息
        "errors": {
            "header_mismatch": "错误：期望的标题为 {expected}，实际为 {actual}",
            "general_error": "错误：{error}",
            "no_human_readable_id": "无法提取可读 ID"
        }
    },
    
    # 浏览提示词 Tab
    "browse": {
        "tab_title": "查看提示词",
        "title": "查看提示词",
        "filter_signature_label": "按签名筛选",
        "sort_by_label": "排序方式",
        "sort_order_label": "排序顺序",
        "all_option": "全部",
        "run_date_option": "运行日期",
        "evaluation_score_option": "评估分数",
        "descending_option": "降序",
        "ascending_option": "升序",
        "view_details_button": "查看详情",
        "close_details_button": "关闭详情",
        
        # 详情字段标签
        "details": {
            "evaluation_score": "评估分数",
            "input_fields": "输入字段",
            "output_fields": "输出字段",
            "module": "模块",
            "model": "模型",
            "teacher_model": "教师模型",
            "optimizer": "优化器",
            "instructions": "指令",
            "optimized_prompt": "优化后的提示词"
        },
        
        # 卡片字段
        "card": {
            "id": "ID",
            "signature": "签名",
            "eval_score": "评估分数"
        }
    }
}