from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import account, auth, carriers, ledger, sessions

app = FastAPI(
    title="ShiftProof — Independent Driver Work Record",
    description=(
        "An independent, verifiable record of work performed by a delivery "
        "driver, kept separate from the contracting carrier's own system. "
        "Your routes. Your work. Your records."
    ),
    version="0.1.0",
)

# The API is called from the React app (browser, and later Capacitor's
# webview) with a Bearer token, never cookies — wildcard origins are safe
# here since allow_credentials stays off.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(account.router)
app.include_router(carriers.router)
app.include_router(sessions.router)
app.include_router(ledger.router)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}
