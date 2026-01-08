# DSPyUI 系统架构图

本文档使用 UML 图展示 DSPyUI 的整体架构设计。

## 1. 系统整体架构（包图）

```mermaid
graph TB
    subgraph "入口层 Entry Points"
        main["main.py<br/>Gradio UI 入口"]
        serve["serve.py<br/>API 服务入口"]
    end
    
    subgraph "dspyui 主包"
        config["config.py<br/>全局配置"]
        
        subgraph "ui/ - Gradio UI 模块"
            ui_app["app.py<br/>主应用组装"]
            ui_tabs["tabs/<br/>Tab 页面"]
            ui_components["components.py<br/>可复用组件"]
            ui_styles["styles.py<br/>CSS 样式"]
            ui_lang["language_switcher.py<br/>语言切换"]
        end
        
        subgraph "api/ - FastAPI REST 模块"
            api_app["app.py<br/>FastAPI 入口"]
            api_routes["routes/<br/>API 路由"]
            api_schemas["schemas.py<br/>数据模型"]
            api_deps["dependencies.py<br/>依赖注入"]
        end
        
        subgraph "core/ - 核心业务逻辑"
            signatures["signatures.py<br/>DSPy Signature"]
            modules["modules.py<br/>DSPy Module"]
            metrics["metrics.py<br/>评估指标"]
            compiler["compiler.py<br/>编译器"]
            runner["runner.py<br/>程序运行器"]
            
            subgraph "MLflow 集成"
                mlflow_tracking["mlflow_tracking.py<br/>实验追踪"]
                mlflow_registry["mlflow_registry.py<br/>模型注册"]
                mlflow_loader["mlflow_loader.py<br/>模型加载"]
                mlflow_service["mlflow_service.py<br/>业务逻辑层"]
            end
            
            subgraph "API 服务核心"
                model_manager["model_manager.py<br/>模型缓存管理"]
                feedback["feedback.py<br/>反馈收集"]
                data_exporter["data_exporter.py<br/>数据导出"]
            end
        end
        
        subgraph "utils/ - 工具函数"
            file_ops["file_ops.py<br/>文件操作"]
            id_generator["id_generator.py<br/>ID 生成"]
        end
        
        subgraph "i18n/ - 国际化"
            i18n_init["__init__.py<br/>翻译服务"]
            zh_CN["zh_CN.py<br/>中文"]
            en_US["en_US.py<br/>英文"]
        end
    end
    
    subgraph "外部依赖"
        dspy["DSPy<br/>LLM 编译框架"]
        mlflow["MLflow<br/>实验追踪"]
        gradio["Gradio<br/>Web UI"]
        fastapi["FastAPI<br/>REST API"]
    end
    
    %% 入口层依赖
    main --> ui_app
    main --> mlflow_tracking
    serve --> api_app
    
    %% UI 模块依赖
    ui_app --> ui_tabs
    ui_app --> ui_components
    ui_app --> ui_styles
    ui_app --> ui_lang
    ui_tabs --> compiler
    ui_tabs --> runner
    ui_tabs --> metrics
    ui_app --> i18n_init
    
    %% API 模块依赖
    api_app --> api_routes
    api_app --> model_manager
    api_app --> feedback
    api_app --> data_exporter
    api_routes --> api_schemas
    api_routes --> api_deps
    
    %% Core 模块依赖
    compiler --> signatures
    compiler --> modules
    compiler --> metrics
    compiler --> mlflow_tracking
    runner --> mlflow_loader
    model_manager --> mlflow_loader
    feedback --> mlflow_tracking
    data_exporter --> mlflow_tracking
    
    %% 外部依赖
    compiler --> dspy
    runner --> dspy
    mlflow_tracking --> mlflow
    ui_app --> gradio
    api_app --> fastapi
```

## 2. 核心类图

```mermaid
classDiagram
    class ModelManager {
        -_cache: Dict
        -_cache_enabled: bool
        -_cache_ttl: int
        -_lock: threading.Lock
        +load_model(name, version, stage, alias) DSPyProgram
        +invalidate_cache(name) void
        +invalidate_all() void
        +get_cache_stats() Dict
    }
    
    class FeedbackService {
        -_feedback_enabled: bool
        +record_feedback(trace_id, rating, corrected_output, comment, user_id) FeedbackRecord
        +validate_trace_exists(trace_id) bool
    }
    
    class FeedbackRecord {
        +trace_id: str
        +rating: str
        +corrected_output: Optional[str]
        +comment: Optional[str]
        +user_id: Optional[str]
        +timestamp: datetime
    }
    
    class DataExporter {
        +query_traces_with_feedback(model_name, rating, start_date, end_date, limit) DataFrame
        +export_training_data(traces_df, format) bytes
        +export_streaming(model_name, rating, format, ...) Generator
    }
    
    class MLflowTracking {
        +init_mlflow() bool
        +track_compilation(experiment_name, run_name) ContextManager
        +log_compilation_metrics(baseline, evaluation, improvement) void
        +log_compilation_artifacts(program_json, dataset_csv) void
        +log_evaluation_table(results) void
        +log_dataset_metadata(row_count, columns, hash) void
        +register_model(run_id, model_name, metadata) ModelVersion
        +transition_model_stage(name, version, stage) void
        +get_mlflow_ui_url(run_id, experiment_id, model_name) str
    }
    
    class Compiler {
        +compile_program(signature, module_type, optimizer, dataset, metric, lm) CompiledProgram
    }
    
    class Runner {
        +generate_program_response(program_json, inputs) str
        +generate_response_from_mlflow(model_uri, inputs) str
        +run_batch_inference_from_mlflow(model_uri, csv_path) DataFrame
        +load_program_metadata(program_json) Dict
        +validate_csv_headers(csv_path, required_headers) bool
    }
    
    FeedbackService --> FeedbackRecord : creates
    ModelManager --> MLflowTracking : uses
    FeedbackService --> MLflowTracking : uses
    DataExporter --> MLflowTracking : uses
    Compiler --> MLflowTracking : uses
    Runner --> MLflowTracking : uses
```

## 3. API 路由结构

```mermaid
classDiagram
    class FastAPIApp {
        +lifespan: AsyncContextManager
        +state.model_manager: ModelManager
        +state.feedback_service: FeedbackService
        +state.data_exporter: DataExporter
    }
    
    class PredictRouter {
        +POST /predict
    }
    
    class FeedbackRouter {
        +POST /feedback
    }
    
    class ExportRouter {
        +GET /export
    }
    
    class ModelsRouter {
        +GET /models
        +GET /models/{name}
        +POST /models/{name}/cache/invalidate
    }
    
    class HealthRouter {
        +GET /health
        +GET /metrics
    }
    
    FastAPIApp --> PredictRouter
    FastAPIApp --> FeedbackRouter
    FastAPIApp --> ExportRouter
    FastAPIApp --> ModelsRouter
    FastAPIApp --> HealthRouter
    
    PredictRouter --> ModelManager : uses
    FeedbackRouter --> FeedbackService : uses
    ExportRouter --> DataExporter : uses
    ModelsRouter --> ModelManager : uses
```

## 4. 数据流图

```mermaid
flowchart LR
    subgraph "用户交互"
        user_ui["用户 (Gradio UI)"]
        user_api["用户 (API Client)"]
    end
    
    subgraph "入口层"
        gradio_app["Gradio App<br/>(main.py)"]
        fastapi_app["FastAPI App<br/>(serve.py)"]
    end
    
    subgraph "核心处理"
        compiler["Compiler<br/>程序编译"]
        runner["Runner<br/>程序执行"]
        model_mgr["ModelManager<br/>模型管理"]
        feedback_svc["FeedbackService<br/>反馈收集"]
        exporter["DataExporter<br/>数据导出"]
    end
    
    subgraph "存储层"
        mlflow_db["MLflow<br/>实验追踪"]
        programs["programs/<br/>程序 JSON"]
        datasets["datasets/<br/>数据集"]
    end
    
    subgraph "外部服务"
        llm["LLM API<br/>(OpenAI/Anthropic/...)"]
    end
    
    %% UI 数据流
    user_ui -->|"编译请求"| gradio_app
    gradio_app -->|"调用"| compiler
    compiler -->|"调用 LLM"| llm
    compiler -->|"保存程序"| programs
    compiler -->|"记录实验"| mlflow_db
    
    user_ui -->|"测试请求"| gradio_app
    gradio_app -->|"调用"| runner
    runner -->|"调用 LLM"| llm
    
    %% API 数据流
    user_api -->|"POST /predict"| fastapi_app
    fastapi_app -->|"加载模型"| model_mgr
    model_mgr -->|"从 MLflow 加载"| mlflow_db
    model_mgr -->|"调用"| runner
    runner -->|"调用 LLM"| llm
    
    user_api -->|"POST /feedback"| fastapi_app
    fastapi_app -->|"记录反馈"| feedback_svc
    feedback_svc -->|"log_feedback"| mlflow_db
    
    user_api -->|"GET /export"| fastapi_app
    fastapi_app -->|"查询导出"| exporter
    exporter -->|"查询 traces"| mlflow_db
```

## 5. 编译流程时序图

```mermaid
sequenceDiagram
    participant User as 用户
    participant UI as Gradio UI
    participant Compiler as compiler.py
    participant MLflow as mlflow_tracking.py
    participant DSPy as DSPy Framework
    participant LLM as LLM API
    
    User->>UI: 配置编译参数
    UI->>Compiler: compile_program()
    
    Compiler->>MLflow: track_compilation() 开始
    MLflow-->>Compiler: 返回 Run 上下文
    
    Compiler->>DSPy: 创建 Signature
    Compiler->>DSPy: 创建 Module
    Compiler->>DSPy: 创建 Optimizer
    
    loop 优化迭代
        DSPy->>LLM: 调用 LLM
        LLM-->>DSPy: 返回响应
        DSPy->>DSPy: 评估指标
    end
    
    DSPy-->>Compiler: 返回编译后程序
    
    Compiler->>MLflow: log_compilation_metrics()
    Compiler->>MLflow: log_compilation_artifacts()
    Compiler->>MLflow: log_evaluation_table()
    Compiler->>MLflow: log_dataset_metadata()
    
    Compiler-->>UI: 返回编译结果
    UI-->>User: 显示结果 + MLflow 链接
```

## 6. API 推理流程时序图

```mermaid
sequenceDiagram
    participant Client as API Client
    participant API as FastAPI
    participant MM as ModelManager
    participant MLflow as MLflow Registry
    participant Runner as runner.py
    participant LLM as LLM API
    participant FB as FeedbackService
    
    Client->>API: POST /predict
    API->>MM: load_model(name, version)
    
    alt 缓存命中
        MM-->>API: 返回缓存模型
    else 缓存未命中
        MM->>MLflow: 加载模型
        MLflow-->>MM: 返回模型
        MM->>MM: 缓存模型
        MM-->>API: 返回模型
    end
    
    API->>Runner: generate_response()
    Runner->>LLM: 调用 LLM
    LLM-->>Runner: 返回响应
    Runner-->>API: 返回结果 + trace_id
    
    API-->>Client: 返回响应
    
    Note over Client,FB: 用户可选择提交反馈
    
    Client->>API: POST /feedback
    API->>FB: record_feedback(trace_id, rating, ...)
    FB->>MLflow: log_feedback()
    FB-->>API: 返回成功
    API-->>Client: 返回确认
```

## 7. 模块依赖关系

```mermaid
graph TD
    subgraph "Layer 1: Entry Points"
        main.py
        serve.py
    end
    
    subgraph "Layer 2: Interface"
        ui/app.py
        api/app.py
    end
    
    subgraph "Layer 3: Business Logic"
        core/compiler.py
        core/runner.py
        core/model_manager.py
        core/feedback.py
        core/data_exporter.py
    end
    
    subgraph "Layer 4: Domain"
        core/signatures.py
        core/modules.py
        core/metrics.py
    end
    
    subgraph "Layer 5: Infrastructure"
        core/mlflow_tracking.py
        core/mlflow_registry.py
        core/mlflow_loader.py
        utils/file_ops.py
    end
    
    subgraph "Layer 6: External"
        DSPy
        MLflow
        Gradio
        FastAPI
        LLM_APIs
    end
    
    main.py --> ui/app.py
    serve.py --> api/app.py
    
    ui/app.py --> core/compiler.py
    ui/app.py --> core/runner.py
    
    api/app.py --> core/model_manager.py
    api/app.py --> core/feedback.py
    api/app.py --> core/data_exporter.py
    
    core/compiler.py --> core/signatures.py
    core/compiler.py --> core/modules.py
    core/compiler.py --> core/metrics.py
    core/compiler.py --> core/mlflow_tracking.py
    
    core/runner.py --> core/mlflow_loader.py
    core/model_manager.py --> core/mlflow_loader.py
    
    core/mlflow_tracking.py --> MLflow
    core/compiler.py --> DSPy
    core/runner.py --> DSPy
    ui/app.py --> Gradio
    api/app.py --> FastAPI
```

## 8. 部署架构

```mermaid
graph TB
    subgraph "用户层"
        browser["浏览器<br/>(Gradio UI)"]
        api_client["API 客户端<br/>(REST)"]
    end
    
    subgraph "应用层"
        gradio_server["Gradio Server<br/>:7860"]
        fastapi_server["FastAPI Server<br/>:8000"]
    end
    
    subgraph "服务层"
        mlflow_server["MLflow Server<br/>:5000"]
    end
    
    subgraph "存储层"
        mlflow_db["mlflow_data/<br/>mlflow.db"]
        mlartifacts["mlartifacts/<br/>模型工件"]
        programs["programs/<br/>程序 JSON"]
        datasets["datasets/<br/>数据集"]
    end
    
    subgraph "外部 API"
        openai["OpenAI API"]
        anthropic["Anthropic API"]
        groq["Groq API"]
        google["Google AI API"]
        deepseek["DeepSeek API"]
    end
    
    browser --> gradio_server
    api_client --> fastapi_server
    
    gradio_server --> mlflow_server
    fastapi_server --> mlflow_server
    
    mlflow_server --> mlflow_db
    mlflow_server --> mlartifacts
    
    gradio_server --> programs
    gradio_server --> datasets
    
    gradio_server --> openai
    gradio_server --> anthropic
    gradio_server --> groq
    gradio_server --> google
    gradio_server --> deepseek
    
    fastapi_server --> openai
    fastapi_server --> anthropic
    fastapi_server --> groq
    fastapi_server --> google
    fastapi_server --> deepseek
```

## 总结

DSPyUI 采用分层架构设计：

| 层级 | 模块 | 职责 |
|------|------|------|
| 入口层 | `main.py`, `serve.py` | 应用启动入口 |
| 接口层 | `ui/`, `api/` | 用户交互界面 |
| 业务层 | `core/compiler.py`, `core/runner.py`, `core/model_manager.py` | 核心业务逻辑 |
| 领域层 | `core/signatures.py`, `core/modules.py`, `core/metrics.py` | DSPy 领域模型 |
| 基础设施层 | `core/mlflow_*.py`, `utils/` | 外部服务集成 |

两个主要入口：
1. **Gradio UI** (`main.py`) - 面向开发者的可视化编译和测试界面
2. **FastAPI API** (`serve.py`) - 面向生产环境的推理服务 API
