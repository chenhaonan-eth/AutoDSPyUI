"""
DSPyUI API 服务启动脚本

INPUT:  dspyui.api.app, dspyui.config, uvicorn
OUTPUT: API 服务启动入口，支持命令行参数配置
POS:    API 服务程序入口点，负责启动 FastAPI 应用

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

import argparse
import logging
import sys

import uvicorn

from dspyui.config import get_api_config

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description="DSPyUI API 服务启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python serve.py                          # 使用默认配置启动
  python serve.py --host 127.0.0.1         # 指定监听地址
  python serve.py --port 8080              # 指定端口
  python serve.py --workers 2              # 指定 worker 数量
  python serve.py --reload                 # 开发模式（自动重载）

环境变量:
  API_HOST              API 服务监听地址 (默认: 0.0.0.0)
  API_PORT              API 服务监听端口 (默认: 8000)
  API_WORKERS           Uvicorn worker 数量 (默认: 4)
  API_REQUEST_TIMEOUT   请求超时时间（秒）(默认: 60)
  MLFLOW_TRACKING_URI   MLflow 追踪服务器地址
  MLFLOW_ENABLED        启用/禁用 MLflow 追踪 (true/false)
        """
    )
    
    # 服务器配置
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="API 服务监听地址 (默认从环境变量 API_HOST 读取，或 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="API 服务监听端口 (默认从环境变量 API_PORT 读取，或 8000)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Uvicorn worker 数量 (默认从环境变量 API_WORKERS 读取，或 4)"
    )
    
    # 开发模式
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载（开发模式，不支持多 worker）"
    )
    
    # 日志级别
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="日志级别 (默认: info)"
    )
    
    return parser.parse_args()


def main() -> None:
    """启动 DSPyUI API 服务"""
    args = parse_args()
    
    # 获取配置（优先使用命令行参数，其次使用环境变量/默认值）
    config = get_api_config()
    
    host = args.host if args.host is not None else config.api_host
    port = args.port if args.port is not None else config.api_port
    workers = args.workers if args.workers is not None else config.api_workers
    
    # 开发模式下只能使用单 worker
    if args.reload and workers > 1:
        logger.warning("开发模式（--reload）不支持多 worker，将使用单 worker")
        workers = 1
    
    logger.info("=" * 60)
    logger.info("DSPyUI API 服务启动")
    logger.info("=" * 60)
    logger.info(f"监听地址: {host}:{port}")
    logger.info(f"Worker 数量: {workers}")
    logger.info(f"请求超时: {config.api_request_timeout}s")
    logger.info(f"开发模式: {'是' if args.reload else '否'}")
    logger.info(f"MLflow URI: {config.mlflow_tracking_uri}")
    logger.info("=" * 60)
    
    try:
        uvicorn.run(
            "dspyui.api.app:app",
            host=host,
            port=port,
            workers=workers if not args.reload else 1,
            reload=args.reload,
            log_level=args.log_level,
        )
    except KeyboardInterrupt:
        logger.info("API 服务已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"API 服务启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
