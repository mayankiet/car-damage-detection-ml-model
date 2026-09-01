
from pathlib import Path
import tempfile
import traceback

import requests
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse

from report_generator import generate_report


# ============================================================
# CONFIGURATION
# ============================================================

PHASE1_API = "http://127.0.0.1:8000"
PHASE2_API = "http://127.0.0.1:8001"
PHASE3_API = "http://127.0.0.1:8002"


app = FastAPI(
    title="Phase 4 - Used Car Assessment",
    version="1.0.0",
)


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "service": "Phase 4 - Used Car Assessment",
        "status": "running",
        "endpoint": "/generate-report",
        "services": {
            "phase1": PHASE1_API,
            "phase2": PHASE2_API,
            "phase3": PHASE3_API,
        },
    }


@app.get("/health")
def health():
    services = {}

    for name, url in {
        "phase1": PHASE1_API,
        "phase2": PHASE2_API,
        "phase3": PHASE3_API,
    }.items():

        try:
            response = requests.get(
                f"{url}/",
                timeout=5,
            )

            services[name] = {
                "available": response.status_code == 200,
                "status_code": response.status_code,
            }

        except Exception as error:

            services[name] = {
                "available": False,
                "error": str(error),
            }

    return {
        "status": "ok",
        "services": services,
    }


# ============================================================
# HELPERS
# ============================================================

def call_phase1(
    file_path: str,
    file_name: str,
    content_type: str | None,
):
    with open(file_path, "rb") as file:

        response = requests.post(
            f"{PHASE1_API}/predict",
            files={
                "file": (
                    file_name,
                    file,
                    content_type or "application/octet-stream",
                )
            },
            timeout=120,
        )

    try:
        data = response.json()
    except Exception:
        data = {
            "success": False,
            "error": response.text,
            "error_type": "InvalidJSONResponse",
        }

    if response.status_code != 200:

        raise RuntimeError(
            f"Phase 1 returned HTTP {response.status_code}: {data}"
        )

    return data


def call_phase2(
    file_path: str,
    file_name: str,
    content_type: str | None,
):
    with open(file_path, "rb") as file:

        response = requests.post(
            f"{PHASE2_API}/analyze",
            files={
                "file": (
                    file_name,
                    file,
                    content_type or "application/octet-stream",
                )
            },
            timeout=240,
        )

    try:
        data = response.json()
    except Exception:
        data = {
            "success": False,
            "error": response.text,
            "error_type": "InvalidJSONResponse",
        }

    if response.status_code != 200:

        raise RuntimeError(
            f"Phase 2 returned HTTP {response.status_code}: {data}"
        )

    return data


def call_phase3(
    phase2_response: dict,
    phase1_response: dict,
    city: str | None,
    mileage_km: float | None,
    owner_serial: str | None,
):
    fields = (
        phase2_response.get(
            "extracted_fields",
            {},
        )
        or {}
    )

    manufacturer = fields.get(
        "manufacturer"
    )

    model = fields.get(
        "model"
    )

    # Phase 3 accepts an optional explicit variant. For the RC
    # pipeline the exact model/variant may already be contained
    # in the model value, so variant is optional.
    variant = fields.get(
        "variant"
    )

    vehicle = {
        "registration_number":
            fields.get(
                "registration_number"
            ),

        "manufacturer":
            manufacturer,

        "model":
            model,

        "variant":
            variant,

        "manufacturing_date":
            fields.get(
                "manufacturing_date"
            ),

        "registration_date":
            fields.get(
                "registration_date"
            ),

        "fuel_type":
            fields.get(
                "fuel_type"
            ),

        "owner_serial":
            owner_serial
            or
            fields.get(
                "owner_serial"
            ),

        "city":
            city or "Delhi",

        "mileage_km":
            mileage_km,
    }

    damage = {
        "predicted_class":
            phase1_response.get(
                "predicted_class"
            )
            or
            phase1_response.get(
                "class_name"
            ),

        "confidence":
            phase1_response.get(
                "confidence"
            ),
    }

    response = requests.post(
        f"{PHASE3_API}/valuate",
        json={
            "vehicle": vehicle,
            "damage": damage,
        },
        timeout=90,
    )

    try:
        data = response.json()
    except Exception:
        data = {
            "success": False,
            "error": response.text,
            "error_type": "InvalidJSONResponse",
        }

    if response.status_code != 200:

        raise RuntimeError(
            f"Phase 3 returned HTTP {response.status_code}: {data}"
        )

    return data


# ============================================================
# FINAL REPORT
# ============================================================

@app.post("/generate-report")
async def generate_report_endpoint(
    damage_image: UploadFile = File(...),
    document: UploadFile = File(...),
    city: str | None = Form(default=None),
    mileage_km: float | None = Form(default=None),
    owner_serial: str | None = Form(default=None),
):
    damage_path = None
    document_path = None

    try:

        # ----------------------------------------------------
        # Save Phase 1 image
        # ----------------------------------------------------

        damage_suffix = (
            Path(
                damage_image.filename or ""
            ).suffix
            or ".jpg"
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=damage_suffix,
        ) as temp:

            temp.write(
                await damage_image.read()
            )

            damage_path = temp.name

        # ----------------------------------------------------
        # Save Phase 2 document
        # ----------------------------------------------------

        document_suffix = (
            Path(
                document.filename or ""
            ).suffix
            or ".jpg"
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=document_suffix,
        ) as temp:

            temp.write(
                await document.read()
            )

            document_path = temp.name

        # ----------------------------------------------------
        # Phase 1
        # ----------------------------------------------------

        phase1_response = call_phase1(
            damage_path,
            damage_image.filename or "damage.jpg",
            damage_image.content_type,
        )

        # ----------------------------------------------------
        # Phase 2
        # ----------------------------------------------------

        phase2_response = call_phase2(
            document_path,
            document.filename or "document",
            document.content_type,
        )

        # ----------------------------------------------------
        # Phase 3
        # ----------------------------------------------------

        phase3_response = call_phase3(
            phase2_response,
            phase1_response,
            city,
            mileage_km,
            owner_serial,
        )

        # ----------------------------------------------------
        # Professional report
        # ----------------------------------------------------

        final_report = generate_report(
            phase1_response,
            phase2_response,
        )

        # Add valuation as a business result without exposing
        # the raw Phase 1/2 API payloads.
        final_report["valuation"] = phase3_response

        # Keep the final report business-facing.
        return final_report

    except Exception as error:

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(error),
                "error_type": type(error).__name__,
                "phase": "Phase 4",
                "debug": {
                    "traceback": traceback.format_exc(),
                },
            },
        )

    finally:

        if damage_path:
            Path(
                damage_path
            ).unlink(
                missing_ok=True
            )

        if document_path:
            Path(
                document_path
            ).unlink(
                missing_ok=True
            )
