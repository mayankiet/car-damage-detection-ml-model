
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from valuation_engine import evaluate_vehicle


app = FastAPI(
    title="Phase 3 - Used Car Valuation API",
    version="1.0.0",
)


class VehicleData(BaseModel):
    registration_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    manufacturing_date: Optional[str] = None
    registration_date: Optional[str] = None
    fuel_type: Optional[str] = None
    owner_serial: Optional[str] = None
    city: Optional[str] = "Delhi"
    mileage_km: Optional[float] = Field(
        default=None,
        ge=0,
    )


class DamageData(BaseModel):
    predicted_class: Optional[str] = None
    confidence: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )


class ValuationRequest(BaseModel):
    vehicle: VehicleData
    damage: DamageData = DamageData()


@app.get("/")
def root():
    return {
        "service": "Phase 3 - Used Car Valuation",
        "status": "running",
        "endpoint": "/valuate",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "phase3",
    }


@app.post("/valuate")
def valuate(request: ValuationRequest):
    return evaluate_vehicle(
        vehicle=request.vehicle.model_dump(),
        damage=request.damage.model_dump(),
    )
