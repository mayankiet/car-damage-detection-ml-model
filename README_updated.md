# Axis Used Car Assessment

A multi-phase used-car assessment prototype combining vehicle damage detection, document intelligence, market-reference valuation, and final PDF reporting.

## Architecture

| Phase | Function | FastAPI Port |
|---|---|---:|
| Phase 1 | Vehicle damage detection | 8000 |
| Phase 2 | RC / document intelligence using Gemini | 8001 |
| Phase 3 | Market reference & valuation | 8002 |
| Phase 4 | Combined assessment & report generation | 8003 |

```text
Vehicle Image
     |
     v
Phase 1 :8000
Damage Detection
     |
     | damage result
     v
Phase 4 :8003 <---------------- RC / Document
     ^                              |
     |                              v
     |                        Phase 2 :8001
     |                        Gemini 3.6 Flash
     |                              |
     |                       vehicle/document data
     |                              v
     +------------------------ Phase 3 :8002
                              Market Valuation
                                     |
                                  valuation
                                     v
                              Phase 4 :8003
                                     |
                                     v
                           Professional PDF Report
```

## Project Structure

```text
car-damage-detection-ml-model/
├── .gitignore
├── README.md
├── app.py
├── app_screenshot.jpg
├── car_damage_detection.ipynb
│
├── datasets/
│   ├── F_Breakage/          (~268 images: FB_1.jpg - FB_268.jpg)
│   ├── F_Crushed/           (~200+ images)
│   ├── F_Normal/            (~200+ images)
│   ├── R_Breakage/          (~200+ images)
│   ├── R_Crushed/           (~200+ images)
│   └── R_Normal/            (~200+ images)
│
├── phase2/
│   ├── PHASE2_README.md
│   ├── api.py
│   ├── requirements.txt
│   ├── streamlit_app.py
│   └── app/
│       ├── __init__.py
│       └── analyzer.py
│
├── phase4/
│   ├── api.py
│   ├── phase4_streamlit_app.py
│   └── report_generator.py
│
├── training/
│   └── car_damage_detection.ipynb
│
├── .git/
├── .idea/
├── .venv/
└── __pycache__/
```

`/.venv`, `/.git`, `/.idea`, and `__pycache__` are local/development directories.

> Note: the Phase 3 code and market-reference CSV should be placed in `phase3/` if you are using the Phase 3 implementation described below.

---

# 1. Prerequisites

Recommended:

- Python 3.11+
- Git
- Gemini API key for Phase 2
- Trained Phase 1 model/checkpoint required by the existing model code

---

# 2. Create the Virtual Environment

From the project root:

```bash
cd ~/Documents/car-damage-detection-ml-model
```

Create it:

```bash
python3 -m venv .venv
```

Activate it on macOS / Linux:

```bash
source .venv/bin/activate
```

Upgrade pip:

```bash
pip install --upgrade pip
```

---

# 3. Install Dependencies

Install the common packages:

```bash
pip install fastapi uvicorn streamlit requests python-multipart reportlab
```

Install Gemini:

```bash
pip install -U google-genai
```

Install Phase 1 dependencies:

```bash
pip install torch torchvision pillow
```

Phase 2 also contains:

```text
phase2/requirements.txt
```

Install those with:

```bash
cd phase2
pip install -r requirements.txt
cd ..
```

---

# 4. Configure Gemini

Gemini is used only in Phase 2.

Set the key:

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

Verify:

```bash
python -c "import os; print('Gemini key loaded:', bool(os.getenv('GEMINI_API_KEY')))"
```

Expected:

```text
Gemini key loaded: True
```

Phase 2 uses:

```text
gemini-3.6-flash
```

When opening a new terminal, activate the virtual environment and make sure `GEMINI_API_KEY` is available there before starting Phase 2.

---

# 5. Phase 1 — Vehicle Damage Detection

Phase 1 is the PyTorch / ResNet vehicle damage classifier.

Configured classes:

```text
Front Breakage
Front Crushed
Front Normal
Rear Breakage
Rear Crushed
Rear Normal
```

Dataset structure:

```text
datasets/
├── F_Breakage/
├── F_Crushed/
├── F_Normal/
├── R_Breakage/
├── R_Crushed/
└── R_Normal/
```

Training notebooks:

```text
car_damage_detection.ipynb
training/car_damage_detection.ipynb
```

The current API entry point is:

```text
phase1_api.py
```

Start Phase 1 on port 8000:

```bash
cd ~/Documents/car-damage-detection-ml-model
source .venv/bin/activate
uvicorn phase1_api:app --reload --port 8000
```

Endpoints:

```text
GET  /health
POST /predict
```

Phase 1 expects the trained model/checkpoint required by `model_helper.py`.

Check for it:

```bash
find ~/Documents/car-damage-detection-ml-model   -name "saved_model.pth"   -o -name "*.pth"   -o -name "*.pt"
```

---

# 6. Phase 2 — Document Intelligence

Phase 2 uses Gemini 3.6 Flash to extract information from RC / insurance / claim documents.

Structure:

```text
phase2/
├── PHASE2_README.md
├── api.py
├── requirements.txt
├── streamlit_app.py
└── app/
    ├── __init__.py
    └── analyzer.py
```

Start Phase 2 on port 8001:

```bash
cd ~/Documents/car-damage-detection-ml-model/phase2
source ../.venv/bin/activate
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
uvicorn api:app --reload --port 8001
```

Endpoint:

```text
POST /analyze
```

Phase 2 is designed to recognize RC labels and abbreviations such as:

```text
Regn. Number
Regd Owner
Regn. Date
Manufacturing Dt.
Regd Validity
Vehicle Class
Body Type
Manufacturer
Chassis No
Engine No.
Model No
Tax Paid Up To
Hypothecated To
Cubic Capacity
Seat Capacity
No. Of Cylinders
Wheel Base
R.L.W.
Owner Serial
```

The response contains fields such as:

```text
document_type
extracted_fields
missing_information
completeness_score
risk_status
review_flags
summary
```

---

# 7. Phase 3 — Market Reference & Valuation

Phase 3 uses market-reference data and a transparent valuation engine.

Recommended structure:

```text
phase3/
├── market_reference.csv
├── phase3_api.py
├── phase3_streamlit_app.py
└── valuation_engine.py
```

The market CSV should be:

```text
phase3/market_reference.csv
```

Expected columns:

```text
brand
model
variant
year
fuel
city
min_price_inr
median_price_inr
max_price_inr
source
source_date
```

The current prototype reference data contains multiple brands and models and is labelled as illustrative market-reference data.

Start Phase 3 on port 8002:

```bash
cd ~/Documents/car-damage-detection-ml-model/phase3
source ../.venv/bin/activate
uvicorn phase3_api:app --reload --port 8002
```

Important: the current Phase 3 API filename is `phase3_api.py`, so use:

```bash
uvicorn phase3_api:app --reload --port 8002
```

Endpoints:

```text
GET  /
GET  /health
POST /valuate
```

The valuation flow is:

```text
Vehicle information
       +
Market reference records
       +
Age
Mileage
Ownership
Damage
       |
       v
Estimated Fair Value
```

The prototype adjustment percentages are business assumptions for demonstration and should not be presented as measured market statistics.

---

# 8. Phase 4 — Combined Assessment

Phase 4 is the orchestration/reporting layer.

Current structure:

```text
phase4/
├── api.py
├── phase4_streamlit_app.py
└── report_generator.py
```

Start Phase 4 on port 8003:

```bash
cd ~/Documents/car-damage-detection-ml-model/phase4
source ../.venv/bin/activate
uvicorn api:app --reload --port 8003
```

Endpoints:

```text
GET  /
GET  /health
POST /generate-report
```

Phase 4 calls:

```text
Phase 1 → http://127.0.0.1:8000
Phase 2 → http://127.0.0.1:8001
Phase 3 → http://127.0.0.1:8002
```

It then combines the results into a final business-facing assessment.

---

# 9. Phase 4 Streamlit UI

The final Streamlit application is:

```text
phase4/phase4_streamlit_app.py
```

Run:

```bash
cd ~/Documents/car-damage-detection-ml-model/phase4
source ../.venv/bin/activate
streamlit run phase4_streamlit_app.py
```

The UI is organized into:

```text
Phase 1 — Damage Detection
Phase 2 — Document Intelligence
Phase 3 — Market Valuation
Phase 4 — Final Assessment
```

The final report is presented as a professional PDF.

---

# 10. PDF Report

Phase 4 uses ReportLab.

Install:

```bash
pip install reportlab
```

Verify:

```bash
python -c "import reportlab; print('ReportLab OK')"
```

The PDF contains business-facing information such as:

```text
Vehicle Profile
Vehicle Identifiers
Damage Assessment
Document Assessment
Extracted RC Information
Market Valuation
Valuation Adjustments
Market Comparables
Final Assessment
Recommendation
```

It intentionally does not expose:

```text
Raw API JSON
OCR dumps
FastAPI debug output
Technical tracebacks
Internal API responses
```

---

# 11. Start the Full System

Use five terminals.

## Terminal 1 — Phase 1

```bash
cd ~/Documents/car-damage-detection-ml-model
source .venv/bin/activate
uvicorn phase1_api:app --reload --port 8000
```

## Terminal 2 — Phase 2

```bash
cd ~/Documents/car-damage-detection-ml-model/phase2
source ../.venv/bin/activate
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
uvicorn api:app --reload --port 8001
```

## Terminal 3 — Phase 3

```bash
cd ~/Documents/car-damage-detection-ml-model/phase3
source ../.venv/bin/activate
uvicorn phase3_api:app --reload --port 8002
```

## Terminal 4 — Phase 4

```bash
cd ~/Documents/car-damage-detection-ml-model/phase4
source ../.venv/bin/activate
uvicorn api:app --reload --port 8003
```

## Terminal 5 — Phase 4 Streamlit

```bash
cd ~/Documents/car-damage-detection-ml-model/phase4
source ../.venv/bin/activate
streamlit run phase4_streamlit_app.py
```

---

# 12. Verify the APIs

Run:

```bash
curl http://127.0.0.1:8000/
```

```bash
curl http://127.0.0.1:8001/
```

```bash
curl http://127.0.0.1:8002/
```

```bash
curl http://127.0.0.1:8003/
```

For Phase 4:

```bash
curl http://127.0.0.1:8003/health
```

The Phase 4 health endpoint checks whether Phase 1, Phase 2 and Phase 3 are reachable.

---

# 13. End-to-End Flow

The final user flow is:

```text
Vehicle damage image
        |
        v
Phase 1 :8000
        |
        v
Damage classification

RC / vehicle document
        |
        v
Phase 2 :8001
        |
        v
Vehicle/document information

Phase 1 + Phase 2 information
        |
        v
Phase 3 :8002
        |
        v
Market valuation

Phase 1 + Phase 2 + Phase 3
        |
        v
Phase 4 :8003
        |
        v
Professional combined PDF report
```

---

# 14. Troubleshooting

## Phase 1 model file not found

Run:

```bash
find ~/Documents/car-damage-detection-ml-model   -name "saved_model.pth"   -o -name "*.pth"   -o -name "*.pt"
```

The model/checkpoint must be available to the Phase 1 inference code.

## Phase 2 Gemini key missing

Check:

```bash
echo $GEMINI_API_KEY
```

Then:

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

Verify:

```bash
python -c "import os; print(bool(os.getenv('GEMINI_API_KEY')))"
```

## Phase 3 cannot import the API

Check the filename:

```text
phase3/phase3_api.py
```

Start with:

```bash
uvicorn phase3_api:app --reload --port 8002
```

## Phase 3 cannot find market data

Check:

```bash
ls -lh ~/Documents/car-damage-detection-ml-model/phase3/market_reference.csv
```

## Phase 4 cannot connect

Check:

```bash
curl http://127.0.0.1:8003/
```

Then:

```bash
curl http://127.0.0.1:8003/health
```

## PDF generation fails

Install:

```bash
pip install reportlab
```

Verify:

```bash
python -c "import reportlab; print('ReportLab OK')"
```

---

# 15. Port Summary

```text
Phase 1 FastAPI → 8000
Phase 2 FastAPI → 8001
Phase 3 FastAPI → 8002
Phase 4 FastAPI → 8003
```

Streamlit runs separately from the FastAPI ports.

---

# 16. Hackathon Demo

For the final demo:

1. Start Phase 1, Phase 2, Phase 3 and Phase 4 FastAPI services.
2. Start the Phase 4 Streamlit UI.
3. Upload the vehicle damage image.
4. Upload the RC/document.
5. Enter valuation information such as city and mileage.
6. Generate the assessment.
7. View the professional PDF.
8. Download the combined PDF.

The final user-facing experience is:

```text
Upload Vehicle Image
        +
Upload RC / Document
        +
Valuation Inputs
        |
        v
Generate Assessment
        |
        v
Professional PDF Report
```
