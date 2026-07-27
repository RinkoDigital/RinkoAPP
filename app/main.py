from fastapi import FastAPI

from app.routers import clients, companies, deliveries, drivers, reports

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
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok"}
