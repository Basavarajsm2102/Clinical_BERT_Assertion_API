import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .middleware import (
    MetricsMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)

# Custom imports
from .model import ClinicalAssertionModel
from .schemas import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
)
from .utils import apply_hybrid_pipeline, get_system_metrics, sanitize_clinical_text

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)
MODEL_INFERENCE_DURATION = Histogram(
    "model_inference_duration_seconds", "Model inference time"
)
MODEL_PREDICTIONS_TOTAL = Counter(
    "model_predictions_total", "Total model predictions", ["label"]
)

# Global variables
model = None
app_start_time = time.time()
prediction_count = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced application lifespan management"""
    global model

    logger.info("🚀 Starting Clinical BERT API...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

    try:
        # Initialize model
        model = ClinicalAssertionModel()
        await model.load_model()

        # Warm up model
        logger.info("🔥 Warming up model...")
        await model.predict("Test sentence for model warmup.")

        logger.info("✅ Clinical BERT API started successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        raise

    yield

    logger.info("🔄 Shutting down Clinical BERT API...")


# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="Clinical BERT Assertion API",
    description="""
    🏥 **Production-Grade Clinical Text Classification API**

    Real-time inference API for clinical assertion detection using
    `bvanaken/clinical-assertion-negation-bert` from Hugging Face.

    ## Features
    - ⚡ Sub-500ms response time
    - 🔒 Enterprise security
    - 📊 Comprehensive monitoring
    - 🚀 Auto-scaling deployment
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
)

# Add middleware stack
app.add_middleware(
    SecurityHeadersMiddleware,
    csp_policy=(
        "default-src 'self'; script-src 'self' 'unsafe-inline' "
        "https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' https://fastapi.tiangolo.com"
    ),
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"])
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)


@app.get("/health", response_model=HealthResponse, tags=["Health Check"])
async def health_check():
    """Comprehensive health check endpoint"""
    global model, app_start_time, prediction_count

    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    uptime_seconds = time.time() - app_start_time
    system_metrics = get_system_metrics()

    return HealthResponse(
        status="healthy" if model.is_loaded() else "unhealthy",
        model_loaded=model.is_loaded(),
        timestamp=time.time(),
        version="1.0.0",
        uptime_seconds=uptime_seconds,
        total_predictions=prediction_count,
        system_metrics=system_metrics,
    )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict_assertion(
    request: PredictionRequest, background_tasks: BackgroundTasks
):
    """Enhanced prediction endpoint with monitoring"""
    global model, prediction_count

    if not model or not model.is_loaded():
        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="503").inc()
        raise HTTPException(status_code=503, detail="Model not loaded")

    request_id = str(uuid.uuid4())
    sanitized_sentence = sanitize_clinical_text(request.sentence)

    try:
        start_time = time.time()

        logger.info(
            f"Prediction request {request_id}: sentence_length={len(request.sentence)}"
        )

        with MODEL_INFERENCE_DURATION.time():
            model_result = await model.predict(sanitized_sentence)

        # Apply hybrid pipeline for rule-based enhancements
        enhanced_results = apply_hybrid_pipeline([model_result], [sanitized_sentence])
        result = enhanced_results[0]

        prediction_time = time.time() - start_time
        prediction_count += 1

        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="200").inc()
        MODEL_PREDICTIONS_TOTAL.labels(label=result["label"]).inc()

        logger.info(
            f"Prediction completed {request_id}: final_label={result['label']}, "
            f"model_label={result['model_label']}, rule={result.get('rule_applied')}, "
            f"time={prediction_time:.3f}s"
        )

        return PredictionResponse(
            label=result["label"],
            model_label=result["model_label"],
            score=result["score"],
            rule_applied=result["rule_applied"],
            prediction_time_ms=prediction_time * 1000,
            request_id=request_id,
        )

    except Exception as e:
        REQUEST_COUNT.labels(method="POST", endpoint="/predict", status="500").inc()
        logger.error(f"Prediction failed {request_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
async def predict_batch(
    request: BatchPredictionRequest, background_tasks: BackgroundTasks
):
    """Enhanced batch prediction"""
    global model, prediction_count

    if not model or not model.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")

    max_batch_size = int(os.getenv("MAX_BATCH_SIZE", "100"))
    if len(request.sentences) > max_batch_size:
        raise HTTPException(
            status_code=400, detail=f"Batch size cannot exceed {max_batch_size}"
        )

    request_id = str(uuid.uuid4())

    try:
        start_time = time.time()

        sanitized_sentences = [sanitize_clinical_text(s) for s in request.sentences]

        logger.info(
            f"Batch prediction {request_id}: batch_size={len(request.sentences)}"
        )

        with MODEL_INFERENCE_DURATION.time():
            model_results = await model.predict_batch(sanitized_sentences)

        # Apply hybrid pipeline for rule-based enhancements
        enhanced_results = apply_hybrid_pipeline(model_results, sanitized_sentences)

        prediction_time = time.time() - start_time
        prediction_count += len(request.sentences)

        REQUEST_COUNT.labels(
            method="POST", endpoint="/predict/batch", status="200"
        ).inc()
        for result in enhanced_results:
            MODEL_PREDICTIONS_TOTAL.labels(label=result["label"]).inc()

        predictions = [
            PredictionResponse(
                label=result["label"],
                model_label=result["model_label"],
                score=result["score"],
                rule_applied=result["rule_applied"],
                prediction_time_ms=(prediction_time * 1000) / len(enhanced_results),
            )
            for result in enhanced_results
        ]

        logger.info(
            f"Batch prediction completed {request_id}: batch_size={len(enhanced_results)}, time={prediction_time:.3f}s"
        )

        return BatchPredictionResponse(
            predictions=predictions,
            batch_size=len(enhanced_results),
            total_prediction_time_ms=prediction_time * 1000,
            request_id=request_id,
        )

    except Exception as e:
        REQUEST_COUNT.labels(
            method="POST", endpoint="/predict/batch", status="500"
        ).inc()
        logger.error(f"Batch prediction failed {request_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Batch prediction failed: {str(e)}"
        )


@app.get("/", tags=["Root"])
async def root():
    """API information and status"""
    return {
        "name": "Clinical BERT Assertion API",
        "version": "1.0.0",
        "description": "Production-grade clinical text classification API",
        "model": "bvanaken/clinical-assertion-negation-bert",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "status": "healthy" if model and model.is_loaded() else "initializing",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "batch_predict": "/predict/batch",
            "metrics": "/metrics",
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=int(os.getenv("WORKERS", 1)),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
