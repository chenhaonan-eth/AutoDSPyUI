"""
英文翻译字典

INPUT:  无
OUTPUT: TRANSLATIONS 字典
POS:    英文翻译数据，被 i18n.__init__ 模块加载

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

TRANSLATIONS = {
    # Common components
    "common": {
        "language_selector": "Language",
        "chinese": "中文",
        "english": "English"
    },
    
    # Compile Program Tab
    "compile": {
        "tab_title": "Compile Program",
        "title": "DSPyUI: a Gradio user interface for DSPy",
        "subtitle": "Compile a DSPy program by specifying your settings and providing example data.",
        
        # Example buttons
        "examples": {
            "title": "Demo Examples:",
            "judging_jokes": "Judging Jokes",
            "telling_jokes": "Telling Jokes",
            "rewriting_jokes": "Rewriting Jokes"
        },
        
        # Task instructions
        "instructions": {
            "label": "Task Instructions",
            "placeholder": "Enter detailed task instructions here.",
            "info": "Provide clear and comprehensive instructions for the task."
        },
        
        # Input/Output fields
        "inputs": {
            "title": "Inputs",
            "description": "Add input fields for your task.",
            "add_button": "Add Input Field",
            "remove_button": "Remove Last Input",
            "placeholder_name": "Input{i}",
            "placeholder_desc": "Description (optional)",
            "name_info": "Specify the name of this input field.",
            "placeholder_message": "Please add at least one input field."
        },
        
        "outputs": {
            "title": "Outputs",
            "description": "Add output fields for your task.",
            "add_button": "Add Output Field",
            "remove_button": "Remove Last Output",
            "placeholder_name": "Output{i}",
            "placeholder_desc": "Description (optional)",
            "name_info": "Specify the name of this output field.",
            "placeholder_message": "Please add at least one output field."
        },
        
        # Data section
        "data": {
            "title": "Data",
            "description": "Provide example data for your task.",
            "enter_manually": "Enter manually",
            "upload_csv": "Upload CSV",
            "export_csv": "Export to CSV",
            "download_csv": "Download CSV",
            "example_data_label": "Example Data"
        },
        
        # Settings section
        "settings": {
            "title": "Settings",
            "model_label": "Model",
            "model_info": "Select the main language model.",
            "teacher_label": "Teacher",
            "teacher_info": "Select a teacher model for compilation.",
            "module_label": "Module",
            "module_info": "Choose the DSPy module.",
            "hint_label": "Hint",
            "hint_placeholder": "Enter a hint for ChainOfThoughtWithHint.",
            "optimizer_label": "Optimizer",
            "optimizer_info": "Choose optimization strategy.",
            "metric_label": "Metric",
            "metric_info": "Choose evaluation metric.",
            "judge_prompt_label": "Judge Prompt"
        },
        
        # Module options
        "modules": {
            "predict": "Predict",
            "chain_of_thought": "ChainOfThought",
            "chain_of_thought_with_hint": "ChainOfThoughtWithHint"
        },
        
        # Optimizer options
        "optimizers": {
            "bootstrap_few_shot": "BootstrapFewShot",
            "bootstrap_few_shot_with_random_search": "BootstrapFewShotWithRandomSearch",
            "mipro": "MIPRO",
            "miprov2": "MIPROv2",
            "copro": "COPRO"
        },
        
        # Metric options
        "metrics": {
            "exact_match": "Exact Match",
            "cosine_similarity": "Cosine Similarity",
            "llm_as_judge": "LLM-as-a-Judge"
        },
        
        # Buttons
        "buttons": {
            "compile": "Compile Program",
            "generate": "Generate",
            "select_random_row": "Select Random Row"
        },
        
        # Results section
        "results": {
            "title": "Results",
            "signature_label": "Signature",
            "evaluation_score_label": "Evaluation Score",
            "baseline_score_label": "Baseline Score",
            "optimized_prompt_label": "Optimized Prompt",
            "generated_response_label": "Generated Response",
            "select_row_label": "Select a row from the dataset"
        },
        
        # Error messages
        "errors": {
            "header_mismatch": "Error: Expected headers {expected}, got {actual}",
            "general_error": "Error: {error}",
            "no_human_readable_id": "Could not extract human-readable ID"
        }
    },
    
    # Run Program Tab
    "run": {
        "tab_title": "Run Program",
        "title": "Program Runner",
        "subtitle": "Load a compiled DSPy program and run interactive inference.",
        
        # Program selection
        "select_program": "Select Program",
        "select_program_placeholder": "Select a program...",
        "no_programs_available": "No programs available",
        "refresh_programs": "Refresh Program List",
        
        # Program info display
        "program_info": {
            "title": "Program Info",
            "signature": "Signature",
            "model": "Model",
            "teacher_model": "Teacher Model",
            "optimizer": "Optimizer",
            "module": "Module",
            "instructions": "Task Instructions",
            "evaluation_score": "Evaluation Score",
            "baseline_score": "Baseline Score",
            "optimized_prompt": "Optimized Prompt",
            "view_prompt": "View Full Prompt",
            "hide_prompt": "Hide Prompt"
        },
        
        # Input section
        "input_section": {
            "title": "Input",
            "description": "Fill in the required input fields."
        },
        
        # Output section
        "output_section": {
            "title": "Output",
            "description": "Generated output from the program."
        },
        
        # Run buttons and status
        "buttons": {
            "run": "Run",
            "running": "Running...",
            "clear": "Clear",
            "retry": "Retry"
        },
        
        # Mode toggle
        "mode": {
            "single": "Single Inference",
            "batch": "Batch Inference",
            "switch_to_batch": "Switch to Batch Mode",
            "switch_to_single": "Switch to Single Mode"
        },
        
        # Batch processing
        "batch": {
            "title": "Batch Inference",
            "upload_csv": "Upload CSV File",
            "upload_description": "Upload a CSV file containing input data",
            "expected_headers": "Expected Headers",
            "start_batch": "Start Batch Inference",
            "progress": "Progress",
            "processing": "Processing {current}/{total}...",
            "completed": "Batch inference completed",
            "results_preview": "Results Preview",
            "export_results": "Export Results",
            "download_csv": "Download CSV"
        },
        
        # History
        "history": {
            "title": "History",
            "description": "Recent inference records",
            "empty": "No history yet",
            "clear": "Clear History",
            "clear_confirm": "Are you sure you want to clear all history?",
            "timestamp": "Time",
            "click_to_restore": "Click to restore input"
        },
        
        # Error messages
        "errors": {
            "program_not_found": "Program file not found: {path}",
            "metadata_not_found": "Program metadata file not found: {path}",
            "load_failed": "Failed to load program: {error}",
            "inference_failed": "Inference failed: {error}",
            "csv_header_mismatch": "CSV header mismatch. Expected: {expected}, Got: {actual}",
            "csv_upload_failed": "CSV upload failed: {error}",
            "empty_input": "Please fill in all required fields",
            "batch_row_error": "Row {row} processing failed: {error}"
        },
        
        # Success messages
        "success": {
            "inference_complete": "Inference complete",
            "batch_complete": "Batch inference complete, processed {count} records",
            "history_cleared": "History cleared"
        },
        
        # Loading states
        "loading": {
            "program": "Loading program...",
            "inference": "Running inference...",
            "batch": "Processing batch data..."
        }
    },
    
    # Browse Prompts Tab
    "browse": {
        "tab_title": "View Prompts",
        "title": "View Prompts",
        "filter_signature_label": "Filter by Signature",
        "sort_by_label": "Sort by",
        "sort_order_label": "Sort Order",
        "all_option": "All",
        "run_date_option": "Run Date",
        "evaluation_score_option": "Evaluation Score",
        "descending_option": "Descending",
        "ascending_option": "Ascending",
        "view_details_button": "View Details",
        "close_details_button": "Close Details",
        
        # Details field labels
        "details": {
            "evaluation_score": "Evaluation Score",
            "input_fields": "Input Fields",
            "output_fields": "Output Fields",
            "module": "Module",
            "model": "Model",
            "teacher_model": "Teacher Model",
            "optimizer": "Optimizer",
            "instructions": "Instructions",
            "optimized_prompt": "Optimized Prompt"
        },
        
        # Card fields
        "card": {
            "id": "ID",
            "signature": "Signature",
            "eval_score": "Eval Score"
        }
    }
}