import os
import tempfile

from pathlib import Path

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from app.analyzer import analyze_document

app = FastAPI(
    title="Axis Document Intelligence API",
    description="Phase 2 - Insurance Document Intelligence",
    version="1.0"
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".jpg",
    ".jpeg",
    ".png"
}


@app.get("/")
def home():

    return {
        "project": "Axis Document Intelligence",
        "phase": 2,
        "status": "running"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Supported: PDF, DOCX, TXT, JPG, JPEG, PNG"
            )
        )

    contents = await file.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temporary_file:

            temporary_file.write(contents)

            temp_path = temporary_file.name

        result = analyze_document(
            temp_path
        )

        return result

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:

        if temp_path and os.path.exists(temp_path):

            os.remove(temp_path)