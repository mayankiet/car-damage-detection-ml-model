from pathlib import Path
import tempfile
import traceback

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from model_helper import predict


app = FastAPI(
    title="Phase 1 - Car Damage Detection API",
    version="1.0.0",
)


# ============================================================
# HEALTH / DEBUG
# ============================================================

@app.get("/")
def root():
    return {
        "service": "Phase 1 - Car Damage Detection",
        "status": "running",
        "endpoint": "/predict",
    }


@app.get("/health")
def health():
    model_path = (
        Path(__file__).resolve().parent
        / "model"
        / "saved_model.pth"
    )

    return {
        "status": "ok",
        "model_path": str(model_path),
        "model_exists": model_path.exists(),
    }


# ============================================================
# PREDICTION
# ============================================================

@app.post("/predict")
async def predict_damage(
    file: UploadFile = File(...)
):
    temp_path = None

    try:
        # ----------------------------------------------------
        # Validate upload
        # ----------------------------------------------------

        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "No file name was provided.",
                    "error_type": "InvalidUpload",
                    "phase": "Phase 1",
                },
            )

        # ----------------------------------------------------
        # Save uploaded file
        # ----------------------------------------------------

        suffix = (
            Path(file.filename).suffix.lower()
            or ".jpg"
        )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp:

            temp.write(
                await file.read()
            )

            temp_path = temp.name

        # ----------------------------------------------------
        # Run model
        # ----------------------------------------------------

        result = predict(
            temp_path
        )

        # ----------------------------------------------------
        # Support both:
        #   predict() -> string
        # and
        #   predict() -> dict
        # ----------------------------------------------------

        if isinstance(
            result,
            str,
        ):

            return {
                "success": True,
                "phase": "Phase 1",
                "file_name": file.filename,
                "predicted_class": result,
                "confidence": None,
                "debug": {
                    "model_status": "loaded",
                    "prediction_status": "success",
                },
            }

        if isinstance(
            result,
            dict,
        ):

            class_name = (
                result.get("class_name")
                or result.get("predicted_class")
            )

            confidence = result.get(
                "confidence"
            )

            return {
                "success": True,
                "phase": "Phase 1",
                "file_name": file.filename,
                "predicted_class": class_name,
                "confidence": confidence,
                "debug": {
                    "model_status": "loaded",
                    "prediction_status": "success",
                },
            }

        # ----------------------------------------------------
        # Unexpected model return
        # ----------------------------------------------------

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Model returned an unsupported response type.",
                "error_type": "UnexpectedModelResponse",
                "returned_type": type(result).__name__,
                "phase": "Phase 1",
            },
        )

    except FileNotFoundError as error:

        # Most common cause: saved_model.pth not found.
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(error),
                "error_type": "FileNotFoundError",
                "phase": "Phase 1",
                "debug": {
                    "cwd": str(Path.cwd()),
                    "api_file": str(Path(__file__).resolve()),
                    "model_path": str(
                        Path(__file__).resolve().parent
                        / "model"
                        / "saved_model.pth"
                    ),
                },
            },
        )

    except RuntimeError as error:

        # Useful for PyTorch state_dict / architecture problems.
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(error),
                "error_type": "PyTorchRuntimeError",
                "phase": "Phase 1",
                "debug": {
                    "hint": (
                        "Check that model/saved_model.pth was trained "
                        "with the same ResNet architecture and class count."
                    ),
                    "traceback": traceback.format_exc(),
                },
            },
        )

    except Exception as error:

        # Full diagnostic instead of a generic HTTP 500.
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(error),
                "error_type": type(error).__name__,
                "phase": "Phase 1",
                "debug": {
                    "cwd": str(Path.cwd()),
                    "api_file": str(Path(__file__).resolve()),
                    "traceback": traceback.format_exc(),
                },
            },
        )

    finally:

        if temp_path:

            try:
                Path(temp_path).unlink(
                    missing_ok=True
                )
            except Exception:
                pass
