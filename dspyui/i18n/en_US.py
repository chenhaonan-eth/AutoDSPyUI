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
        },
        
        # MLflow integration
        "mlflow": {
            "view_experiment": "View MLflow Experiment",
            "view_run": "View This Run",
            "statistics_recorded": "📊 Statistics recorded to MLflow",
            "no_active_run": "ℹ️ No active MLflow Run, statistics not recorded",
            "recording_failed": "⚠️ MLflow recording failed: {error}",
            "experiment_page_info": "MLflow Experiment Page: {url}",
            "run_page_info": "MLflow Run Page: {url}",
            "model_name_label": "Model Name",
            "model_name_placeholder": "Enter model name",
            "register_model": "Register Model to MLflow",
            "register_model_empty_name": "❌ Please enter model name",
            "register_model_no_run_id": "❌ This compilation has no associated MLflow Run ID, cannot register",
            "register_model_mlflow_disabled": "❌ MLflow is not enabled",
            "register_model_registration_failed": "❌ Model registration failed",
            "register_model_exception": "❌ Registration failed: {error}",
            "register_model_success": "✅ Model registered successfully! Version: {version}",
            "view_model": "View Model"
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
            "eval_score": "Eval Score",
            "registered": "✅ Registered",
            "unregistered": "⚪ Unregistered"
        },
        
        # MLflow integration
        "mlflow": {
            "registered_models_title": "Registered Models",
            "refresh_models": "Refresh Models",
            "model_name_label": "Model Name",
            "model_name_placeholder": "Enter model name",
            "register_model": "Register Model",
            "register_model_empty_name": "❌ Please enter model name",
            "register_model_no_run_id": "❌ This program has no associated MLflow Run ID, cannot register",
            "register_model_failed": "❌ Model registration failed",
            "register_model_error": "❌ Registration failed: {error}",
            "register_model_success": "✅ Model registered successfully! Version: {version}",
            "view_model": "View Model",
            "load_artifact_failed": "❌ Failed to load prompt artifact, please check MLflow run status",
            "model_table_headers": {
                "model_name": "Model Name",
                "version": "Version",
                "stage": "Stage",
                "evaluation_score": "Evaluation Score",
                "creation_time": "Creation Time",
                "run_id": "Run ID"
            }
        }
    },
    
    # Test Model Tab
    "test": {
        "tab_title": "Test Model",
        "title": "Model Testing",
        "description": "Load registered models from MLflow for testing.",
        "mlflow_disabled": "⚠️ MLflow is not enabled, this feature is unavailable.",
        
        # Model selection
        "model_selection": "Model Selection",
        "model_name": "Model Name",
        "model_version": "Version",
        "llm_model": "Inference LLM",
        
        # Single test
        "single_test": "Single Test",
        "select_model_first": "Please select a model first",
        "enter": "Enter",
        "run_test": "Run Test",
        "output": "Output Result",
        
        # Batch test
        "batch_test": "Batch Test",
        "upload_csv": "Upload CSV File",
        "run_batch": "Batch Inference",
        "progress": "Progress",
        "batch_result": "Batch Result",
        "download_result": "Download Result",
        
        # Error messages
        "error_no_file": "Please upload a CSV file first",
        "error_no_model": "Please select a model and version first",
        "error": "Error"
    }
}