from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import auth, clients, companies, deliveries, drivers, me, packages, reports

app = FastAPI(
    title="Rinko Delivery Payment API",
    description=(
        "Registers deliveries, validates them, and calculates how much each "
        "driver is owed per package."
    ),
    version="0.1.0",
)

app.include_router(companies.router)
app.include_router(drivers.router)
app.include_router(clients.router)
app.include_router(deliveries.router)
app.include_router(packages.router)
app.include_router(reports.router)
app.include_router(auth.router)
app.include_router(me.router)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}
