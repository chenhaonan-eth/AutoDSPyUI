"""
API 路由模块

INPUT:  FastAPI APIRouter
OUTPUT: 各功能路由 (predict, feedback, export, models, health)
POS:    路由层，组织和导出所有 API 端点

⚠️ 一旦我被更新，务必更新我的开头注释，以及所属文件夹的 README.md
"""

from dspyui.api.routes.export import router as export_router
from dspyui.api.routes.feedback import router as feedback_router
from dspyui.api.routes.health import router as health_router
from dspyui.api.routes.models import router as models_router
from dspyui.api.routes.predict import router as predict_router

__all__ = [
    "predict_router",
    "feedback_router",
    "export_router",
    "models_router",
    "health_router",
]
