import os
import logging
import uuid
import dspy
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from autodspy import load_model_from_registry, load_model_from_run
from dspyui.config import MLFLOW_TRACKING_URI, MLFLOW_ENABLED

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional MLflow
try:
    import mlflow
    from mlflow.entities import AssessmentSource, AssessmentSourceType
    MLFLOW_INSTALLED = True
except ImportError:
    MLFLOW_INSTALLED = False

app = FastAPI(title="AutoDSPy Deployment Service")

# Global variables for model
current_program = None
model_metadata = {}

class PredictionRequest(BaseModel):
    inputs: Dict[str, Any]

class FeedbackRequest(BaseModel):
    trace_id: str
    name: str = "user_feedback"
    value: Any  # Can be boolean, numeric, or string
    comment: Optional[str] = None
    user_id: Optional[str] = "anonymous"

@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    global current_program
    
    model_uri = os.environ.get("MLFLOW_MODEL_URI")
    if not model_uri:
        logger.warning("MLFLOW_MODEL_URI not set. Service started without a model.")
        return

    try:
        if MLFLOW_ENABLED and MLFLOW_INSTALLED:
            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            
            # Extract name and version from URI if possible
            # Format: models:/name/version or models:/name/stage
            if model_uri.startswith("models:/"):
                parts = model_uri.replace("models:/", "").split("/")
                name = parts[0]
                version = parts[1] if len(parts) > 1 else "latest"
                current_program = load_model_from_registry(name, version=version)
            elif model_uri.startswith("runs:/"):
                parts = model_uri.replace("runs:/", "").split("/")
                run_id = parts[0]
                current_program = load_model_from_run(run_id)
            else:
                # Fallback to direct dspy loading if it's a local path
                current_program = dspy.load(model_uri)
            
            logger.info(f"Successfully loaded model from {model_uri}")
        else:
            # Load local if MLflow is not used
            current_program = dspy.load(model_uri)
            logger.info(f"Successfully loaded local model from {model_uri}")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        # Dont raise exception here to allow service to start and be debugged

@app.post("/predict")
async def predict(request: PredictionRequest):
    """Run DSPy program and return results with a trace_id."""
    if not current_program:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # If MLflow is enabled and we have tracing, use it
        if MLFLOW_ENABLED and MLFLOW_INSTALLED and hasattr(mlflow, "start_trace"):
            with mlflow.start_trace(name="deployment_predict") as trace:
                result = current_program(**request.inputs)
                
                # Result might be a dspy.Prediction or just a value
                output = result.toDict() if hasattr(result, "toDict") else result
                
                return {
                    "result": output,
                    "trace_id": trace.info.request_id
                }
        else:
            # Basic prediction without tracing
            result = current_program(**request.inputs)
            output = result.toDict() if hasattr(result, "toDict") else result
            return {
                "result": output,
                "trace_id": str(uuid.uuid4()) # Pseudo trace_id
            }
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def log_feedback(request: FeedbackRequest):
    """Log user feedback to an existing trace in MLflow."""
    if not MLFLOW_ENABLED or not MLFLOW_INSTALLED:
        raise HTTPException(status_code=501, detail="MLflow feedback not enabled")

    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        
        mlflow.log_feedback(
            trace_id=request.trace_id,
            name=request.name,
            value=request.value,
            rationale=request.comment,
            source=AssessmentSource(
                source_type=AssessmentSourceType.HUMAN,
                source_id=request.user_id
            )
        )
        return {"status": "success", "message": "Feedback logged to MLflow"}
    except Exception as e:
        logger.error(f"Failed to log feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
