# MLflow 集成模块

提供 DSPy 程序与 MLflow 的集成功能，包括实验追踪、模型注册和版本管理。

## 文件清单

| 文件名 | 层级定位 | 核心功能 |
|--------|----------|----------|
| `__init__.py` | 模块入口 | 导出公共 API |
| `tracking.py` | 核心模块 | MLflow 追踪、指标记录、模型别名管理 |
| `loader.py` | 核心模块 | 模型加载、版本查询 |
| `registry.py` | 核心模块 | 模型注册、别名设置 |
| `service.py` | 服务层 | 高级模型注册服务 |

## 核心 API

### 模型别名管理（推荐）

MLflow 2.9.0+ 推荐使用 Alias 机制替代废弃的 Stage API：

```python
from autodspy.mlflow import (
    set_model_alias,
    delete_model_alias,
    get_model_version_by_alias,
    load_model_by_alias,
)

# 设置生产版本
set_model_alias("joke-generator", "champion", "2")

# 设置候选版本
set_model_alias("joke-generator", "challenger", "3")

# 获取版本号
version = get_model_version_by_alias("joke-generator", "champion")

# 加载模型
program = load_model_by_alias("joke-generator", "champion")
# 或
program = load_model_from_registry("joke-generator", alias="champion")
```

### 别名与 Stage 对照

| 旧 Stage (废弃) | 新 Alias (推荐) | 说明 |
|----------------|-----------------|------|
| `Production` | `champion` | 生产环境当前版本 |
| `Staging` | `challenger` | 待验证的候选版本 |
| `Archived` | (删除别名) | 归档版本 |

### 模型 URI 格式

```python
# 使用别名（推荐）
"models:/joke-generator@champion"

# 使用版本号
"models:/joke-generator/2"

# 使用 Stage（已废弃）
"models:/joke-generator/Production"
```

## 配置项

```python
# autodspy/config.py
mlflow_production_alias: str = "champion"   # 生产别名
mlflow_staging_alias: str = "challenger"    # 候选别名
```

环境变量：
- `MLFLOW_PRODUCTION_ALIAS`: 生产别名，默认 "champion"
- `MLFLOW_STAGING_ALIAS`: 候选别名，默认 "challenger"
