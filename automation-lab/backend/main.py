from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
from app.api.endpoints import router as api_router
from app.core.config import settings
from app.utils.startup import init_data_files


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_data_files()
app = FastAPI(title=settings.app_name, version=settings.version)

@app.get("/")
def read_root():
    return {
        "service": "Automation Lab API",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }

# Middleware: Request Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")
    return response

# Middleware: CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)