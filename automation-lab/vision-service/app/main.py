from fastapi import FastAPI
from .api import v1

app = FastAPI(title="vision-service")


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(v1.router, prefix="/api/vision")

