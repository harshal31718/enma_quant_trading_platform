from fastapi import FastAPI

app = FastAPI(
    title="Data Service",
    root_path="/api/data"
)

@app.get("/health")
def health():
    return {"service": "data-service", "status": "ok"}