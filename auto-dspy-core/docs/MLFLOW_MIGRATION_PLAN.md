# MLflow API 迁移计划

## 背景

MLflow 2.9.0 起废弃了 Stage API (`transition_model_version_stage`)，推荐使用 Alias 机制。
同时 MLflow 2.12+ 原生支持 DSPy 模型 (`mlflow.dspy`)。

## 迁移目标

1. 将废弃的 Stage API 迁移到 Alias 机制
2. 采用 `mlflow.dspy.log_model()` 替代自定义 JSON 序列化
3. 使用 `mlflow.dspy.load_model()` 加载模型

## API 变更对照

### Stage → Alias 映射

| 旧 Stage | 新 Alias | 说明 |
|----------|----------|------|
| `Production` | `champion` | 生产环境当前版本 |
| `Staging` | `challenger` | 待验证的候选版本 |
| `Archived` | (删除别名) | 归档版本无需别名 |
| `None` | (无别名) | 开发中版本 |

### API 替换

| 旧 API (废弃) | 新 API |
|--------------|--------|
| `transition_model_version_stage(name, version, "Production")` | `set_registered_model_alias(name, "champion", version)` |
| `transition_model_version_stage(name, version, "Staging")` | `set_registered_model_alias(name, "challenger", version)` |
| `get_latest_versions(name, stages=["Production"])` | `get_model_version_by_alias(name, "champion")` |
| `models:/model_name/Production` | `models:/model_name@champion` |

### DSPy 模型保存/加载

| 旧方式 | 新方式 |
|--------|--------|
| 自定义 JSON 序列化 + `log_artifact()` | `mlflow.dspy.log_model(dspy_module, "model")` |
| 自定义 JSON 反序列化 | `mlflow.dspy.load_model(model_uri)` |

## 需要修改的文件

### 1. `autodspy/mlflow/tracking.py`

- [x] `register_model()`: 添加 `mlflow.dspy.log_model()` 支持
- [x] `transition_model_stage()`: 替换为 `set_registered_model_alias()`
- [x] 新增 `set_model_alias()` 函数
- [x] 新增 `delete_model_alias()` 函数
- [x] 新增 `get_model_version_by_alias()` 函数

### 2. `autodspy/mlflow/loader.py`

- [x] `load_model_from_registry()`: 支持 `alias` 参数
- [x] `load_model_by_alias()`: 新增按别名加载便捷函数
- [x] `list_model_versions()`: 返回 aliases 信息
- [x] `get_model_metadata()`: 返回 aliases 信息

### 3. `autodspy/mlflow/registry.py`

- [x] `transition_model_stage()`: 标记废弃，内部转换为 alias
- [x] 新增 `set_model_alias()` 函数
- [x] 新增 `delete_model_alias()` 函数

### 4. `autodspy/config.py`

- [x] 新增 `mlflow_production_alias` 配置项
- [x] 新增 `mlflow_staging_alias` 配置项

### 5. 测试文件

- [ ] `tests/test_mlflow/test_tracking.py`: 更新测试用例
- [ ] `tests/test_mlflow/test_loader.py`: 更新测试用例
- [ ] `tests/test_mlflow/test_registry.py`: 更新测试用例

## 兼容性考虑

### 向后兼容

- 保留 `transition_model_stage()` 函数签名，内部转换为 alias 操作
- 添加 deprecation warning

### 配置项

新增配置项：
```python
# autodspy/config.py
mlflow_default_production_alias: str = "champion"
mlflow_default_staging_alias: str = "challenger"
```

## 实施步骤

1. **Phase 1**: 更新 `tracking.py` - 添加 alias 函数，保留旧函数兼容
2. **Phase 2**: 更新 `loader.py` - 支持 alias URI 和 `mlflow.dspy.load_model()`
3. **Phase 3**: 更新 `registry.py` - 返回 alias 信息
4. **Phase 4**: 更新测试用例
5. **Phase 5**: 更新文档

## 预期收益

- 使用 MLflow 官方推荐 API，避免未来兼容性问题
- 利用 `mlflow.dspy` 原生支持，简化序列化逻辑
- Alias 机制更灵活，支持自定义别名 (如 `v1-stable`, `experiment-a`)
