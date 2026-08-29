
import json
import os
import re
from pathlib import Path

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash",
)


# ============================================================
# RC FIELD SCHEMA
# ============================================================

RC_FIELDS = [
    "registration_number",
    "owner_name",
    "purpose",
    "registration_date",
    "manufacturing_date",
    "colour",
    "fuel_type",
    "vehicle_class",
    "body_type",
    "manufacturer",
    "chassis_number",
    "engine_number",
    "model",
    "tax_paid_up_to",
    "registration_validity",
    "hypothecated_to",
    "unladen_weight",
    "cubic_capacity",
    "seat_capacity",
    "standing_capacity",
    "number_of_cylinders",
    "wheel_base",
    "rlw",
    "owner_serial",
    "address",
    "issuing_authority",
]


RC_LABEL_HINTS = {
    "registration_number": [
        "Regn. Number",
        "Regn Number",
        "Registration Number",
        "Regn. No.",
    ],
    "owner_name": [
        "Regd. Owner",
        "Registered Owner",
        "Owner",
    ],
    "purpose": [
        "Purpose",
    ],
    "registration_date": [
        "Regn. Date",
        "Regn Date",
        "Registration Date",
    ],
    "manufacturing_date": [
        "Manufacturing Dt.",
        "Manufacturing Dt",
        "Manufacturing Date",
        "Mfg Date",
    ],
    "colour": [
        "Colour",
        "Color",
    ],
    "fuel_type": [
        "Fuel",
    ],
    "vehicle_class": [
        "Vehicle Class",
    ],
    "body_type": [
        "Body Type",
    ],
    "manufacturer": [
        "Manufacturer",
    ],
    "chassis_number": [
        "Chassis No.",
        "Chassis No",
        "Chassis Number",
    ],
    "engine_number": [
        "Engine No.",
        "Engine No",
        "Engine Number",
    ],
    "model": [
        "Model No.",
        "Model No",
        "Model Number",
    ],
    "tax_paid_up_to": [
        "Tax Paid Up To",
        "Tax Paid Upto",
    ],
    "registration_validity": [
        "Regd. Validity",
        "Regn. Validity",
        "Registration Validity",
    ],
    "hypothecated_to": [
        "Hypothecated To",
    ],
    "unladen_weight": [
        "Unladen Wt.",
        "Unladen Wt",
        "Unladen Weight",
    ],
    "cubic_capacity": [
        "Cubic Capacity",
    ],
    "seat_capacity": [
        "Seat Capacity",
    ],
    "standing_capacity": [
        "Stand. Capacity",
        "Stand Capacity",
        "Standing Capacity",
    ],
    "number_of_cylinders": [
        "No. Of Cyc",
        "No Of Cyc",
        "No. Of Cyl",
        "No Of Cyl",
        "Number Of Cylinders",
    ],
    "wheel_base": [
        "Wheel Base",
    ],
    "rlw": [
        "R.L.W.",
        "R.L.W",
        "RLW",
    ],
    "owner_serial": [
        "Owner Serial",
    ],
    "address": [
        "Address",
    ],
    "issuing_authority": [
        "Issuing Authority",
    ],
}


NUMBER_FIELDS = {
    "unladen_weight",
    "cubic_capacity",
    "seat_capacity",
    "standing_capacity",
    "number_of_cylinders",
    "wheel_base",
    "rlw",
    "owner_serial",
}

DATE_FIELDS = {
    "registration_date",
    "registration_validity",
}


# ============================================================
# HELPERS
# ============================================================

def clean(value):
    if value is None:
        return None

    value = str(value).strip()

    if value.lower() in {
        "",
        "null",
        "none",
        "n/a",
        "na",
        "not detected",
        "not available",
        "unknown",
        "-",
    }:
        return None

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip(
        " :|-_,'\""
    ) or None


def normalize_registration(value):
    if not value:
        return None

    value = re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(value).upper(),
    )

    match = re.search(
        r"[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{3,5}",
        value,
    )

    return match.group(0) if match else None


def normalize_date(value):
    if not value:
        return None

    value = (
        str(value)
        .upper()
        .replace("O", "0")
        .replace("I", "1")
        .replace("L", "1")
        .replace("-", "/")
        .replace(".", "/")
    )

    match = re.search(
        r"(\d{1,2})/(\d{1,2})/(\d{4})",
        value,
    )

    if not match:
        return None

    day = int(match.group(1))
    month = int(match.group(2))
    year = int(match.group(3))

    if not (
        1 <= day <= 31
        and 1 <= month <= 12
        and 1900 <= year <= 2100
    ):
        return None

    return f"{day:02d}/{month:02d}/{year}"


def normalize_month_year(value):
    if not value:
        return None

    value = (
        str(value)
        .upper()
        .replace("O", "0")
        .replace("I", "1")
        .replace("L", "1")
        .replace("-", "/")
        .replace(".", "/")
    )

    match = re.search(
        r"(\d{1,2})/(\d{4})",
        value,
    )

    if not match:
        return None

    month = int(match.group(1))
    year = int(match.group(2))

    if not (
        1 <= month <= 12
        and 1900 <= year <= 2100
    ):
        return None

    return f"{month:02d}/{year}"


def normalize_number(value):
    if not value:
        return None

    value = str(value).strip()

    # Permit numeric values only.
    if not re.fullmatch(r"\d+", value):
        return None

    return value


def normalize_chassis(value):
    if not value:
        return None

    value = re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(value).upper(),
    )

    if not (
        10 <= len(value) <= 25
    ):
        return None

    if not re.search(r"[A-Z]", value):
        return None

    if not re.search(r"\d", value):
        return None

    return value


def normalize_engine(value):
    if not value:
        return None

    value = re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(value).upper(),
    )

    if not (
        5 <= len(value) <= 25
    ):
        return None

    if not re.search(r"\d", value):
        return None

    return value


def normalize_fuel(value):
    if not value:
        return None

    upper = str(value).upper()

    for fuel in [
        "DIESEL",
        "PETROL",
        "CNG",
        "LPG",
        "ELECTRIC",
        "HYBRID",
    ]:
        if fuel in upper:
            return fuel.title()

    return None


def normalize_field(
    field,
    value,
):
    if not value:
        return None

    if field == "registration_number":
        return normalize_registration(value)

    if field in DATE_FIELDS:
        return normalize_date(value)

    if field == "manufacturing_date":
        return normalize_month_year(value)

    if field in NUMBER_FIELDS:
        return normalize_number(value)

    if field == "chassis_number":
        return normalize_chassis(value)

    if field == "engine_number":
        return normalize_engine(value)

    if field == "fuel_type":
        return normalize_fuel(value)

    return clean(value)


# ============================================================
# GEMINI PROMPT
# ============================================================

def build_gemini_prompt():

    schema_lines = []

    for field in RC_FIELDS:

        labels = ", ".join(
            RC_LABEL_HINTS[field]
        )

        schema_lines.append(
            f'    "{field}": null  '
            f"(label examples: {labels})"
        )

    return f"""
You are a document-understanding system.

Analyze the uploaded image as a vehicle Registration Certificate
(RC). READ THE IMAGE VISUALLY. Understand the printed form layout,
labels, columns, rows, and which value belongs to which label.

Return ONLY a JSON object using exactly these fields:

{{
{",\n".join(schema_lines)}
}}

Rules:

1. Extract only information visible on the uploaded document.
2. Never invent or guess any value.
3. Never copy a value from a neighboring field.
4. The exact label determines the field, not just physical
   closeness.
5. Keep Chassis No. separate from Engine No.
6. Keep Model No. separate from Manufacturer.
7. Keep Regn. Date separate from Manufacturing Dt.
8. Keep Regd. Validity separate from Tax Paid Up To.
9. Keep the lower numeric values matched to their printed labels.
10. Preserve alphanumeric identifiers carefully.
11. Do not create fields outside the schema.
12. Do not include S/D/W of as a field.
13. For unreadable or absent values, return null.
14. Do not "repair" uncertain characters unless the image makes
    the character reasonably clear.
15. The output must be valid JSON.
"""


# ============================================================
# GEMINI EXTRACTION
# ============================================================

def extract_with_gemini(
    file_path
):

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        return (
            None,
            "GEMINI_API_KEY is not set."
        )

    try:

        from google import genai
        from google.genai import types

    except ImportError:

        return (
            None,
            (
                "google-genai is not installed. "
                "Run: pip install google-genai"
            )
        )

    path = Path(
        file_path
    )

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    mime_type = mime_types.get(
        path.suffix.lower()
    )

    if not mime_type:

        return (
            None,
            "Gemini image extraction requires JPG, JPEG, PNG or WEBP."
        )

    try:

        image_bytes = path.read_bytes()

        client = genai.Client(
            api_key=api_key
        )

        # Use a simple JSON object schema that is compatible with
        # the Gemini Python SDK across current versions.
        #
        # Every property is a STRING. Missing/unreadable values are
        # represented by an empty string and converted to None after
        # the response is parsed. This avoids SDK validation issues
        # around nullable array-style JSON schema declarations.
        properties = {}

        for field in RC_FIELDS:

            properties[field] = {
                "type": "STRING",
                "description": (
                    f"Value for RC field {field}. "
                    f"Return an empty string when unreadable or absent."
                ),
            }

        response_schema = {
            "type": "OBJECT",
            "properties": properties,
        }

        response = client.models.generate_content(

            model=GEMINI_MODEL,

            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                build_gemini_prompt(),
            ],

            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0,
            ),
        )

        raw = getattr(
            response,
            "text",
            None
        )

        if not raw:

            return (
                None,
                "Gemini returned an empty response."
            )

        try:

            data = json.loads(
                raw
            )

        except json.JSONDecodeError:

            start = raw.find("{")
            end = raw.rfind("}")

            if (
                start == -1
                or
                end == -1
            ):

                return (
                    None,
                    "Gemini returned invalid JSON."
                )

            data = json.loads(
                raw[
                    start:end + 1
                ]
            )

        return data, None

    except Exception as error:

        return (
            None,
            f"Gemini extraction failed: {error}"
        )


# ============================================================
# VALIDATE GEMINI RESULT
# ============================================================

def validate_gemini_result(
    data
):

    fields = {
        field: None
        for field in RC_FIELDS
    }

    if not isinstance(
        data,
        dict
    ):
        return fields

    for field in RC_FIELDS:

        value = data.get(
            field
        )

        fields[field] = normalize_field(
            field,
            value,
        )

    # --------------------------------------------------------
    # Critical cross-field protection
    # --------------------------------------------------------

    chassis = fields[
        "chassis_number"
    ]

    engine = fields[
        "engine_number"
    ]

    if chassis and engine and chassis == engine:

        # Do not silently assign it to another field.
        fields[
            "engine_number"
        ] = None

    return fields


# ============================================================
# LOCAL FALLBACK
# ============================================================

def extract_with_tesseract(
    file_path
):

    try:

        import cv2
        import pytesseract

    except ImportError as error:

        return (
            {
                field: None
                for field in RC_FIELDS
            },
            f"Local OCR unavailable: {error}"
        )

    image = cv2.imread(
        str(file_path)
    )

    if image is None:

        return (
            {
                field: None
                for field in RC_FIELDS
            },
            "Could not read image."
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    height, width = gray.shape

    if width < 2200:

        scale = 2200 / width

        gray = cv2.resize(
            gray,
            (
                int(width * scale),
                int(height * scale),
            ),
            interpolation=cv2.INTER_CUBIC,
        )

    text = pytesseract.image_to_string(
        gray,
        config="--psm 6",
    )

    fields = {
        field: None
        for field in RC_FIELDS
    }

    patterns = {

        "registration_number":
            [
                r"Regn\.?\s*Number\s*[:\-]?\s*"
                r"([A-Z]{2}\d{1,2}[A-Z]{1,3}\d{3,5})",

                r"\b([A-Z]{2}\d{1,2}[A-Z]{1,3}\d{3,5})\b",
            ],

        "registration_date":
            [
                r"Regn\.?\s*Date\s*[:\-]?\s*"
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
            ],

        "manufacturing_date":
            [
                r"Manufacturing\s*Dt\.?\s*[:\-]?\s*"
                r"(\d{1,2}[/-]\d{4})",
            ],

        "registration_validity":
            [
                r"Reg[dn]\.?\s*Validity\s*[:\-]?\s*"
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
            ],

        "chassis_number":
            [
                r"Chassis\s*No\.?\s*[:\-]?\s*"
                r"([A-Z0-9]{10,25})",
            ],

        "engine_number":
            [
                r"Engine\s*No\.?\s*[:\-]?\s*"
                r"([A-Z0-9]{5,25})",
            ],
    }

    for field, field_patterns in patterns.items():

        for pattern in field_patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if not match:
                continue

            candidate = normalize_field(
                field,
                match.group(1)
            )

            if candidate:

                fields[field] = candidate

                break

    fuel = re.search(
        r"\b(DIESEL|PETROL|CNG|LPG|ELECTRIC|HYBRID)\b",
        text,
        re.IGNORECASE,
    )

    if fuel:

        fields[
            "fuel_type"
        ] = normalize_fuel(
            fuel.group(1)
        )

    generic = {

        "owner_name":
            r"Regd\.?\s*Owner\s*[:\-]?\s*(.+)",

        "purpose":
            r"Purpose\s*[:\-]?\s*(.+)",

        "colour":
            r"(?:Colour|Color)\s*[:\-]?\s*(.+)",

        "vehicle_class":
            r"Vehicle\s*Class\s*[:\-]?\s*(.+)",

        "body_type":
            r"Body\s*Type\s*[:\-]?\s*(.+)",

        "manufacturer":
            r"Manufacturer\s*[:\-]?\s*(.+)",

        "model":
            r"Model\s*No\.?\s*[:\-]?\s*(.+)",

        "tax_paid_up_to":
            r"Tax\s*Paid\s*Up\s*To\s*[:\-]?\s*(.+)",

        "hypothecated_to":
            r"Hypothecated\s*To\s*[:\-]?\s*(.+)",

        "address":
            r"Address\s*[:\-]?\s*(.+)",

        "issuing_authority":
            r"Issuing\s*Authority\s*[:\-]?\s*(.+)",
    }

    for field, pattern in generic.items():

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        candidate = clean(
            match.group(1)
        )

        if candidate:

            fields[field] = candidate

    if (
        fields["chassis_number"]
        and
        fields["engine_number"]
        and
        fields["chassis_number"]
        ==
        fields["engine_number"]
    ):

        fields[
            "engine_number"
        ] = None

    return fields, text


# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyze_document(
    file_path: str
):

    path = Path(
        file_path
    )

    extension = path.suffix.lower()

    if extension not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }:

        # Preserve basic text-document compatibility.
        text = extract_text(
            file_path
        )

        document_type = detect_document_type(
            text
        )

        return {

            "file_name":
                path.name,

            "document_type":
                document_type,

            "summary":
                (
                    f"The uploaded document was identified "
                    f"as '{document_type}'."
                ),

            "extracted_fields":
                {},

            "missing_information":
                [],

            "completeness_score":
                0,

            "risk_status":
                "Review Required",

            "review_flags":
                [],

            "text_preview":
                text[:10000],
        }

    # --------------------------------------------------------
    # Vision first
    # --------------------------------------------------------

    data, vision_error = extract_with_gemini(
        file_path
    )

    if data is not None:

        fields = validate_gemini_result(
            data
        )

        method = (
            f"Gemini API / {GEMINI_MODEL}"
        )

        preview = (
            "Gemini vision extraction was used.\n\n"
            f"Model: {GEMINI_MODEL}"
        )

    else:

        # ----------------------------------------------------
        # Fallback
        # ----------------------------------------------------

        fields, ocr_text = extract_with_tesseract(
            file_path
        )

        method = "Tesseract fallback"

        preview = (
            "Gemini vision was unavailable.\n\n"
            f"Reason: {vision_error}\n\n"
            "LOCAL OCR\n"
            "=========\n"
            f"{ocr_text[:10000]}"
        )

    # --------------------------------------------------------
    # Completeness
    # --------------------------------------------------------

    detected = sum(
        bool(value)
        for value in fields.values()
    )

    total = len(
        RC_FIELDS
    )

    completeness = int(
        detected /
        total *
        100
    )

    # --------------------------------------------------------
    # Missing
    # --------------------------------------------------------

    missing = [

        field.replace(
            "_",
            " "
        ).title()

        for field in RC_FIELDS

        if not fields.get(
            field
        )
    ]

    # --------------------------------------------------------
    # Review flags
    # --------------------------------------------------------

    flags = []

    critical = [
        "registration_number",
        "registration_date",
        "chassis_number",
        "engine_number",
    ]

    for field in critical:

        if not fields.get(
            field
        ):

            flags.append(
                f"{field.replace('_', ' ').title()} "
                "could not be confidently extracted."
            )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if completeness >= 85:

        status = "Ready for Review"

    elif completeness >= 60:

        status = "Review Required"

    else:

        status = "Incomplete"

    # --------------------------------------------------------
    # Debug field list
    # --------------------------------------------------------

    debug = [
        f"Extraction method: {method}",
        "",
    ]

    for field in RC_FIELDS:

        debug.append(
            f"{field}: {fields.get(field)}"
        )

    debug.extend([
        "",
        "RAW / DIAGNOSTIC",
        "================",
        preview[:12000],
    ])

    return {

        "file_name":
            path.name,

        "document_type":
            "RC / Registration Certificate",

        "summary":
            (
                f"RC analysis completed using "
                f"{method}. "
                f"{detected} of {total} configured "
                f"fields were extracted."
            ),

        "extracted_fields":
            fields,

        "missing_information":
            missing,

        "completeness_score":
            completeness,

        "risk_status":
            status,

        "review_flags":
            flags,

        "text_preview":
            "\n".join(debug)[:15000],

        "extraction_method":
            method,
    }
