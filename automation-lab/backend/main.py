from fastapi import FastAPI

app = FastAPI(title="Automation Lab API")

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