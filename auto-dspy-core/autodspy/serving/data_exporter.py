"""
高质量数据导出服务

INPUT:  MLflow Tracing API, traces with feedback
OUTPUT: DataExporter 类，提供 query_traces_with_feedback(), export_training_data() 方法
POS:    核心服务层，负责查询和导出高质量训练数据，被 API 路由层调用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any, Dict, Iterator, List, Literal, Optional

import pandas as pd

from autodspy.config import get_config

# 可选导入 MLflow
try:
    import mlflow
    from mlflow import MlflowClient
    MLFLOW_INSTALLED = True
except ImportError:
    mlflow = None
    MlflowClient = None
    MLFLOW_INSTALLED = False

# 设置日志
logger = logging.getLogger(__name__)


class DataExporter:
    """
    高质量数据导出服务
    
    从 MLflow 查询带有用户反馈的 traces，并导出为训练数据格式。
    支持按反馈评分过滤、日期范围过滤，以及 CSV/JSON 格式导出。
    
    Example:
        >>> exporter = DataExporter()
        >>> df = exporter.query_traces_with_feedback(
        ...     model_name="joke-generator",
        ...     rating="thumbs_up"
        ... )
        >>> data = exporter.export_training_data(df, format="csv")
    """
    
    def __init__(self):
        """初始化 DataExporter"""
        logger.info("DataExporter 初始化")
    
    def _is_available(self) -> bool:
        """检查 MLflow 是否可用"""
        return get_config().mlflow_enabled and MLFLOW_INSTALLED
    
    def query_traces_with_feedback(
        self,
        model_name: Optional[str] = None,
        rating: str = "thumbs_up",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        查询带有指定反馈的 traces
        
        使用 mlflow.search_traces() 过滤带有用户反馈的推理记录。
        
        Args:
            model_name: 模型名称过滤（可选）
            rating: 反馈评分过滤，"thumbs_up" 或 "thumbs_down"
            start_date: 开始日期过滤（可选）
            end_date: 结束日期过滤（可选）
            limit: 返回记录数量限制
            
        Returns:
            包含 traces 数据的 DataFrame，列包括:
            - trace_id: trace ID
            - inputs: 输入字段（JSON 字符串）
            - outputs: 输出字段（JSON 字符串）
            - corrected_output: 修正输出（如果有）
            - rating: 用户评分
            - comment: 用户评论（如果有）
            - timestamp: 时间戳
            - model_name: 模型名称
        """
        if not self._is_available():
            logger.warning("MLflow 不可用，返回空 DataFrame")
            return pd.DataFrame()
        
        try:
            client = MlflowClient()
            
            # 构建过滤条件
            filter_parts = []
            
            # 按反馈评分过滤
            # MLflow 的 feedback 过滤语法: feedback.name = 'value'
            rating_value = "true" if rating == "thumbs_up" else "false"
            filter_parts.append(f"feedback.user_rating = {rating_value}")
            
            # 按模型名称过滤（如果提供）
            if model_name:
                filter_parts.append(f"tags.model_name = '{model_name}'")
            
            # 按日期范围过滤
            if start_date:
                start_ts = int(start_date.timestamp() * 1000)
                filter_parts.append(f"timestamp >= {start_ts}")
            
            if end_date:
                end_ts = int(end_date.timestamp() * 1000)
                filter_parts.append(f"timestamp <= {end_ts}")
            
            filter_string = " AND ".join(filter_parts) if filter_parts else ""
            
            logger.info(f"查询 traces: filter={filter_string}, limit={limit}")
            
            # 执行查询
            traces = mlflow.search_traces(
                filter_string=filter_string,
                max_results=limit
            )
            
            if traces.empty:
                logger.info("未找到匹配的 traces")
                return pd.DataFrame()
            
            # 处理查询结果
            records = []
            for _, trace_row in traces.iterrows():
                record = self._process_trace_row(trace_row, client)
                if record:
                    records.append(record)
            
            df = pd.DataFrame(records)
            logger.info(f"查询到 {len(df)} 条 traces")
            return df
            
        except Exception as e:
            logger.error(f"查询 traces 失败: {e}")
            return pd.DataFrame()
    
    def _process_trace_row(
        self,
        trace_row: pd.Series,
        client: Any
    ) -> Optional[Dict[str, Any]]:
        """
        处理单个 trace 行，提取所需字段
        
        Args:
            trace_row: trace 数据行
            client: MLflow client
            
        Returns:
            处理后的记录字典，如果处理失败返回 None
        """
        try:
            trace_id = trace_row.get("trace_id", "")
            
            # 提取输入输出
            inputs = self._extract_trace_io(trace_row, "inputs")
            outputs = self._extract_trace_io(trace_row, "outputs")
            
            # 提取反馈信息
            assessments = trace_row.get("assessments", [])
            rating = self._extract_assessment_value(assessments, "user_rating")
            corrected_output = self._extract_assessment_value(assessments, "corrected_output")
            comment = self._extract_assessment_value(assessments, "user_comment")
            
            # 提取元数据
            tags = trace_row.get("tags", {}) or {}
            model_name = tags.get("model_name", "")
            
            timestamp = trace_row.get("timestamp_ms", 0)
            if timestamp:
                timestamp = datetime.fromtimestamp(timestamp / 1000).isoformat()
            
            return {
                "trace_id": trace_id,
                "inputs": json.dumps(inputs, ensure_ascii=False) if inputs else "",
                "outputs": json.dumps(outputs, ensure_ascii=False) if outputs else "",
                "corrected_output": json.dumps(corrected_output, ensure_ascii=False) if corrected_output else "",
                "rating": "thumbs_up" if rating else "thumbs_down",
                "comment": comment or "",
                "timestamp": timestamp,
                "model_name": model_name,
            }
            
        except Exception as e:
            logger.warning(f"处理 trace 行失败: {e}")
            return None
    
    def _extract_trace_io(
        self,
        trace_row: pd.Series,
        field: str
    ) -> Optional[Dict[str, Any]]:
        """
        从 trace 行提取输入或输出
        
        Args:
            trace_row: trace 数据行
            field: "inputs" 或 "outputs"
            
        Returns:
            输入/输出字典
        """
        try:
            value = trace_row.get(field)
            if value is None:
                return None
            if isinstance(value, str):
                return json.loads(value)
            if isinstance(value, dict):
                return value
            return None
        except Exception:
            return None
    
    def _extract_assessment_value(
        self,
        assessments: List[Any],
        assessment_name: str
    ) -> Optional[Any]:
        """
        从 assessments 列表中提取指定名称的值
        
        Args:
            assessments: assessment 列表
            assessment_name: 要提取的 assessment 名称
            
        Returns:
            assessment 值，如果未找到返回 None
        """
        if not assessments:
            return None
        
        try:
            for assessment in assessments:
                if isinstance(assessment, dict):
                    if assessment.get("name") == assessment_name:
                        return assessment.get("value")
                elif hasattr(assessment, "name") and assessment.name == assessment_name:
                    return assessment.value
            return None
        except Exception:
            return None
    
    def export_training_data(
        self,
        traces_df: pd.DataFrame,
        format: Literal["csv", "json"] = "csv",
        use_corrected_output: bool = True
    ) -> bytes:
        """
        将 traces 转换为训练数据格式
        
        优先使用 corrected_output（如果有），否则使用原始 output。
        
        Args:
            traces_df: 包含 traces 数据的 DataFrame
            format: 输出格式，"csv" 或 "json"
            use_corrected_output: 是否优先使用修正输出
            
        Returns:
            导出数据的字节流
        """
        if traces_df.empty:
            if format == "csv":
                return b"inputs,outputs\n"
            else:
                return b"[]"
        
        # 准备训练数据
        training_records = []
        
        for _, row in traces_df.iterrows():
            # 解析输入
            inputs = row.get("inputs", "")
            if isinstance(inputs, str) and inputs:
                try:
                    inputs = json.loads(inputs)
                except json.JSONDecodeError:
                    inputs = {"input": inputs}
            elif not inputs:
                inputs = {}
            
            # 解析输出（优先使用修正输出）
            outputs = None
            if use_corrected_output:
                corrected = row.get("corrected_output", "")
                if corrected:
                    try:
                        outputs = json.loads(corrected) if isinstance(corrected, str) else corrected
                    except json.JSONDecodeError:
                        pass
            
            if outputs is None:
                raw_outputs = row.get("outputs", "")
                if isinstance(raw_outputs, str) and raw_outputs:
                    try:
                        outputs = json.loads(raw_outputs)
                    except json.JSONDecodeError:
                        outputs = {"output": raw_outputs}
                elif isinstance(raw_outputs, dict):
                    outputs = raw_outputs
                else:
                    outputs = {}
            
            # 构建训练记录
            record = {**inputs, **outputs}
            
            # 添加元数据（可选）
            if row.get("trace_id"):
                record["_trace_id"] = row["trace_id"]
            if row.get("rating"):
                record["_rating"] = row["rating"]
            
            training_records.append(record)
        
        # 导出为指定格式
        if format == "csv":
            return self._export_csv(training_records)
        else:
            return self._export_json(training_records)
    
    def _export_csv(self, records: List[Dict[str, Any]]) -> bytes:
        """导出为 CSV 格式"""
        if not records:
            return b"inputs,outputs\n"
        
        # 收集所有字段
        all_fields = set()
        for record in records:
            all_fields.update(record.keys())
        
        # 排序字段（元数据字段放最后）
        regular_fields = sorted([f for f in all_fields if not f.startswith("_")])
        meta_fields = sorted([f for f in all_fields if f.startswith("_")])
        fieldnames = regular_fields + meta_fields
        
        # 写入 CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        
        for record in records:
            # 将复杂值转换为 JSON 字符串
            row = {}
            for key, value in record.items():
                if isinstance(value, (dict, list)):
                    row[key] = json.dumps(value, ensure_ascii=False)
                else:
                    row[key] = value
            writer.writerow(row)
        
        return output.getvalue().encode("utf-8")
    
    def _export_json(self, records: List[Dict[str, Any]]) -> bytes:
        """导出为 JSON 格式"""
        return json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8")
    
    def export_streaming(
        self,
        traces_df: pd.DataFrame,
        format: Literal["csv", "json"] = "csv",
        use_corrected_output: bool = True,
        chunk_size: int = 100
    ) -> Iterator[bytes]:
        """
        流式导出训练数据
        
        适用于大数据量导出，避免内存溢出。
        
        Args:
            traces_df: 包含 traces 数据的 DataFrame
            format: 输出格式
            use_corrected_output: 是否优先使用修正输出
            chunk_size: 每批处理的记录数
            
        Yields:
            数据块字节流
        """
        if traces_df.empty:
            if format == "csv":
                yield b"inputs,outputs\n"
            else:
                yield b"[]"
            return
        
        total_rows = len(traces_df)
        
        if format == "json":
            yield b"[\n"
        
        first_chunk = True
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk_df = traces_df.iloc[start_idx:end_idx]
            
            # 导出当前块
            chunk_data = self.export_training_data(
                chunk_df,
                format=format,
                use_corrected_output=use_corrected_output
            )
            
            if format == "csv":
                if first_chunk:
                    yield chunk_data
                else:
                    # 跳过后续块的 header
                    lines = chunk_data.decode("utf-8").split("\n")
                    if len(lines) > 1:
                        yield "\n".join(lines[1:]).encode("utf-8")
            else:
                # JSON 格式需要处理数组分隔
                json_str = chunk_data.decode("utf-8")
                # 移除首尾的 [ ]
                json_str = json_str.strip()[1:-1].strip()
                if json_str:
                    if not first_chunk:
                        yield b",\n"
                    yield json_str.encode("utf-8")
            
            first_chunk = False
        
        if format == "json":
            yield b"\n]"
