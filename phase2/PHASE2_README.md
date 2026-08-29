# Phase 2 — Axis Document Intelligence

Phase 2 is the document-processing component of the project. It provides a FastAPI backend and a Streamlit UI for uploading and analyzing vehicle and insurance documents.

The current RC extraction uses **Google Gemini 3.6 Flash** through the Gemini API. The uploaded document image is sent directly to the vision model so it can understand the document layout and associate each printed label with its corresponding value.

---

## 1. Project Structure

```text
car-damage-detection-ml-model/
├── .venv/
└── phase2/
    ├── api.py
    ├── streamlit_app.py
    └── app/
        └── analyzer.py
```

The commands below assume the project is located at:

```text
~/Documents/car-damage-detection-ml-model
```

---

# 2. Create the Virtual Environment

From the project root:

```bash
cd ~/Documents/car-damage-detection-ml-model (replace it with your project path)
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

After activation, your terminal should show:

```text
(.venv)
```

## Activating the environment later

Whenever you open a new terminal:

```bash
cd ~/Documents/car-damage-detection-ml-model (replace it with your project path)
source .venv/bin/activate
```

---

# 3. Install Dependencies

With the virtual environment activated:

```bash
pip install --upgrade pip
```

Install the Phase 2 dependencies:

```bash
pip install fastapi uvicorn streamlit requests python-multipart
pip install google-genai
pip install opencv-python numpy pillow pytesseract
pip install pymupdf python-docx
```

The main AI dependency for the current RC pipeline is:

```text
google-genai
```

---

# 4. Gemini API Key

The RC vision extractor uses the Gemini API.

You need a Gemini API key from Google AI Studio.

Set the key in the terminal before starting FastAPI:

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

Set the model explicitly:

```bash
export GEMINI_MODEL="gemini-3.6-flash"
```

Verify that the key is available without printing the key itself:

```bash
python -c "import os; print('Gemini key loaded:', bool(os.getenv('GEMINI_API_KEY')))"
```

Expected:

```text
Gemini key loaded: True
```

Verify the Google SDK:

```bash
python -c "from google import genai; print('google-genai OK')"
```

Expected:

```text
google-genai OK
```

> **Security:** Do not commit your Gemini API key to GitHub or put it directly into `analyzer.py`.

---

# 5. Optional: Make the Gemini Key Persistent

If you do not want to run `export` every time, add the environment variable to your shell configuration.

On macOS with zsh:

```bash
nano ~/.zshrc
```

Add:

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export GEMINI_MODEL="gemini-3.6-flash"
```

Save and reload:

```bash
source ~/.zshrc
```

Then verify:

```bash
python -c "import os; print('Gemini key loaded:', bool(os.getenv('GEMINI_API_KEY')))"
```

---

# 6. Start FastAPI

Open **Terminal 1**.

Activate the environment:

```bash
cd ~/Documents/car-damage-detection-ml-model  (replace it with your project path)
source .venv/bin/activate
```

Make sure the Gemini variables are available:

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export GEMINI_MODEL="gemini-3.6-flash"
```

Go to Phase 2:

```bash
cd phase2
```

Start FastAPI:

```bash
uvicorn api:app --reload
```

You should see something similar to:

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

Keep this terminal running.

## Test FastAPI

Open:

```text
http://127.0.0.1:8000/
```

You can also run:

```bash
curl http://127.0.0.1:8000/
```

If your API has a health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

---

# 7. Start Streamlit

Open **Terminal 2**.

Activate the same environment:

```bash
cd ~/Documents/car-damage-detection-ml-model (replace it with your project path)
source .venv/bin/activate
```

Go to Phase 2:

```bash
cd phase2
```

Start Streamlit:

```bash
streamlit run streamlit_app.py
```

You should see a URL similar to:

```text
Local URL: http://localhost:8501
```

Open the URL in your browser.

---

# 8. Run the Complete Phase 2 Application

Two terminals are required.

## Terminal 1 — FastAPI

```bash
cd ~/Documents/car-damage-detection-ml-model (replace it with your project path)
source .venv/bin/activate
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export GEMINI_MODEL="gemini-3.6-flash"
cd phase2
uvicorn api:app --reload
```

## Terminal 2 — Streamlit

```bash
cd ~/Documents/car-damage-detection-ml-model (replace it with your project path)
source .venv/bin/activate
cd phase2
streamlit run streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

The Streamlit frontend communicates with FastAPI at:

```text
http://127.0.0.1:8000
```

---

# 9. How Document Analysis Works

The current Phase 2 flow is:

```text
                 ┌─────────────────────┐
                 │     Streamlit UI    │
                 │   localhost:8501    │
                 └──────────┬──────────┘
                            │
                            │ HTTP POST
                            ▼
                 ┌─────────────────────┐
                 │       FastAPI       │
                 │   localhost:8000    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     analyzer.py     │
                 └──────────┬──────────┘
                            │
                   Original document image
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Gemini 3.6 Flash  │
                 │   Vision + JSON     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Field validation    │
                 │ + completeness      │
                 │ + review flags      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     Streamlit       │
                 │ Structured results  │
                 └─────────────────────┘
```

For RC images, Gemini receives the original image and is instructed to visually understand the label/value relationships rather than treating the page as a flat OCR text stream.

---

# 10. RC Extraction

The RC analyzer currently supports common labels such as:

```text
Regn. Number
Regd. Owner
Purpose
Regn. Date
Manufacturing Dt.
Colour
Fuel
Vehicle Class
Body Type
Manufacturer
Chassis No.
Engine No.
Model No.
Tax Paid Up To
Regd. Validity
Hypothecated To
Unladen Wt
Cubic Capacity
Seat Capacity
Stand. Capacity
No. Of Cyc
Wheel Base
R.L.W.
Owner Serial
Address
Issuing Authority
```

`S/D/W of` is intentionally not exposed as a separate output field.

The application does not hard-code the actual values of any sample RC. Values are read from the uploaded document.

---

# 11. Important Extraction Rules

The vision prompt instructs Gemini to:

- Read the entire RC image.
- Associate values with their printed labels.
- Keep Chassis No. separate from Engine No.
- Keep Model No. separate from Manufacturer.
- Keep Regn. Date separate from Manufacturing Dt.
- Keep Regd. Validity separate from Tax Paid Up To.
- Match lower numeric values to their actual printed labels.
- Avoid guessing or inventing unreadable values.
- Return an empty/missing value when information cannot be confidently read.

The Python analyzer also validates fields such as:

```text
Registration Number
Dates
Manufacturing Month/Year
Numeric fields
Chassis Number
Engine Number
Fuel Type
```

---

# 12. Using the Application

1. Open the Streamlit application.
2. Upload the **original document image**.
3. Click **Analyze Document**.
4. FastAPI sends the document to the analyzer.
5. The analyzer sends the image to Gemini 3.6 Flash.
6. Gemini returns structured JSON.
7. The analyzer validates the values.
8. Streamlit displays:
   - Document type
   - Extracted fields
   - Completeness score
   - Missing information
   - Review flags
   - OCR/diagnostic text
   - JSON response

For RC testing, use the original image instead of a screenshot of the Streamlit page.

---

# 13. Checking Which Extraction Method Was Used

Open:

```text
🔧 View JSON Response
```

The current RC implementation should report:

```json
"extraction_method": "Gemini API / gemini-3.6-flash"
```

If Gemini cannot be used, the analyzer falls back to local Tesseract OCR and reports:

```json
"extraction_method": "Tesseract fallback"
```

If you see the fallback unexpectedly, check:

```bash
python -c "import os; print(bool(os.getenv('GEMINI_API_KEY')))"
```

and verify that FastAPI was started from the same environment where the key is available.

---

# 14. Stop the Servers

To stop FastAPI or Streamlit:

```text
Ctrl + C
```

Run this in the terminal where the service is running.

---

# 15. Common Problems

## `ModuleNotFoundError: No module named 'google'`

Install the Gemini SDK:

```bash
pip install google-genai
```

---

## `GEMINI_API_KEY is not set`

Set the key in the same terminal that starts FastAPI:

```bash
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

Verify:

```bash
python -c "import os; print(bool(os.getenv('GEMINI_API_KEY')))"
```

Expected:

```text
True
```

---

## Gemini returns an error

Check the model variable:

```bash
echo $GEMINI_MODEL
```

Expected:

```text
gemini-3.6-flash
```

You can set it again:

```bash
export GEMINI_MODEL="gemini-3.6-flash"
```

---

## The app is using Tesseract fallback

Check:

```bash
python -c "import os; print('KEY:', bool(os.getenv('GEMINI_API_KEY'))); print('MODEL:', os.getenv('GEMINI_MODEL'))"
```

Also check the FastAPI terminal for Gemini errors.

---

## `No module named 'cv2'`

Run:

```bash
pip install opencv-python
```

---

## `No module named 'pytesseract'`

Run:

```bash
pip install pytesseract
```

---

## `tesseract: command not found`

On macOS:

```bash
brew install tesseract
```

Verify:

```bash
tesseract --version
```

Tesseract is only the local fallback for the current image extraction pipeline.

---

## `Streamlit says File does not exist`

Make sure you are inside:

```text
~/Documents/car-damage-detection-ml-model/phase2
```

Then:

```bash
streamlit run streamlit_app.py
```

---

## `Cannot connect to FastAPI`

Make sure Terminal 1 is running:

```bash
uvicorn api:app --reload
```

Check:

```text
http://127.0.0.1:8000/
```

Also verify the FastAPI URL in the Streamlit sidebar.

Default:

```text
http://127.0.0.1:8000
```

---

## `Address already in use`

Another process may already be using the port.

Stop the existing process:

```text
Ctrl + C
```

Then start the service again.

---

# 16. Quick Start After Initial Setup

Once Python packages and the Gemini API key are configured:

## Terminal 1

```bash
cd ~/Documents/car-damage-detection-ml-model
source .venv/bin/activate
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export GEMINI_MODEL="gemini-3.6-flash"
cd phase2
uvicorn api:app --reload
```

## Terminal 2

```bash
cd ~/Documents/car-damage-detection-ml-model
source .venv/bin/activate
cd phase2
streamlit run streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

---

# 17. Git / Security

Do not commit API keys or uploaded customer documents.

Recommended `.gitignore` entries:

```text
.venv/
__pycache__/
*.pyc
.env
uploads/
```

For a persistent local setup, an environment file can be used, but it must remain outside version control.

---

## Phase 2 Technology Stack

```text
Frontend
    Streamlit

Backend
    FastAPI + Uvicorn

Vision / Document Understanding
    Google Gemini 3.6 Flash

Local Fallback OCR
    Tesseract

Image Processing
    OpenCV + Pillow

Python Environment
    .venv
```

---

**Axis Document Intelligence — Phase 2 Hackathon Prototype**
