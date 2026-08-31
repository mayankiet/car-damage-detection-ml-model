
import json
from datetime import datetime
from pathlib import Path


# ============================================================
# PHASE 4 — PROFESSIONAL REPORT GENERATOR
# ============================================================
#
# Input:
#   Phase 1 FastAPI response
#   Phase 2 FastAPI response
#
# Output:
#   Business-facing assessment report only.
#
# Raw API responses, OCR text and technical/debug details are
# intentionally NOT included in the final report.
# ============================================================


RC_FIELD_ORDER = [
    "registration_number",
    "purpose",
    "manufacturing_date",
    "fuel_type",
    "body_type",
    "chassis_number",
    "model",
    "registration_validity",
    "unladen_weight",
    "seat_capacity",
    "number_of_cylinders",
    "rlw",
    "address",
    "owner_name",
    "registration_date",
    "colour",
    "vehicle_class",
    "manufacturer",
    "engine_number",
    "tax_paid_up_to",
    "hypothecated_to",
    "cubic_capacity",
    "standing_capacity",
    "wheel_base",
    "owner_serial",
    "issuing_authority",
]


def safe_dict(value):
    return value if isinstance(value, dict) else {}


def clean_value(value):
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        return value if value else None

    return value


def confidence_percentage(value):
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if 0 <= number <= 1:
        number *= 100

    return round(
        max(0, min(100, number)),
        2,
    )


def damage_severity(predicted_class):
    if not predicted_class:
        return "Unknown"

    value = str(
        predicted_class
    ).lower()

    if "normal" in value:
        return "Normal"

    if "breakage" in value:
        return "High"

    if "crushed" in value:
        return "High"

    return "Unknown"


def normalize_damage_class(value):
    value = clean_value(value)

    return (
        value
        if value
        else "Not available"
    )


def document_status(
    completeness,
    risk_status,
):
    risk_status = clean_value(
        risk_status
    )

    if risk_status:
        return str(
            risk_status
        )

    try:
        score = float(
            completeness or 0
        )
    except (TypeError, ValueError):
        score = 0

    if score >= 75:
        return "Ready for Review"

    if score >= 50:
        return "Review Required"

    return "Incomplete"


def deduplicate(items):
    result = []
    seen = set()

    for item in items or []:

        item = clean_value(
            item
        )

        if not item:
            continue

        key = str(
            item
        ).lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(
            str(item)
        )

    return result


# ============================================================
# VEHICLE INFORMATION
# ============================================================

def build_vehicle_information(
    phase2
):
    fields = safe_dict(
        phase2.get(
            "extracted_fields"
        )
    )

    return {
        "registration_number":
            clean_value(
                fields.get(
                    "registration_number"
                )
            ),

        "owner_name":
            clean_value(
                fields.get(
                    "owner_name"
                )
            ),

        "manufacturer":
            clean_value(
                fields.get(
                    "manufacturer"
                )
            ),

        "model":
            clean_value(
                fields.get(
                    "model"
                )
            ),

        "fuel_type":
            clean_value(
                fields.get(
                    "fuel_type"
                )
            ),

        "manufacturing_date":
            clean_value(
                fields.get(
                    "manufacturing_date"
                )
            ),

        "colour":
            clean_value(
                fields.get(
                    "colour"
                )
            ),

        "vehicle_class":
            clean_value(
                fields.get(
                    "vehicle_class"
                )
            ),

        "body_type":
            clean_value(
                fields.get(
                    "body_type"
                )
            ),

        "purpose":
            clean_value(
                fields.get(
                    "purpose"
                )
            ),
    }


def build_identifiers(
    phase2
):
    fields = safe_dict(
        phase2.get(
            "extracted_fields"
        )
    )

    return {
        "chassis_number":
            clean_value(
                fields.get(
                    "chassis_number"
                )
            ),

        "engine_number":
            clean_value(
                fields.get(
                    "engine_number"
                )
            ),
    }


# ============================================================
# DOCUMENT ASSESSMENT
# ============================================================

def build_document_assessment(
    phase2
):
    phase2 = safe_dict(
        phase2
    )

    completeness = phase2.get(
        "completeness_score",
        0,
    )

    return {
        "document_type":
            phase2.get(
                "document_type",
                "Unknown",
            ),

        "completeness_score":
            completeness,

        "risk_status":
            document_status(
                completeness,
                phase2.get(
                    "risk_status"
                ),
            ),

        "missing_information":
            deduplicate(
                phase2.get(
                    "missing_information",
                    [],
                )
            ),

        "review_flags":
            deduplicate(
                phase2.get(
                    "review_flags",
                    [],
                )
            ),
    }


# ============================================================
# FULL STRUCTURED DOCUMENT FIELDS
# ============================================================

def build_document_fields(
    phase2
):
    fields = safe_dict(
        phase2.get(
            "extracted_fields"
        )
    )

    return {
        field: clean_value(
            fields.get(
                field
            )
        )
        for field in RC_FIELD_ORDER
    }


# ============================================================
# DAMAGE ASSESSMENT
# ============================================================

def build_damage_assessment(
    phase1
):
    phase1 = safe_dict(
        phase1
    )

    predicted_class = (
        phase1.get(
            "predicted_class"
        )
        or
        phase1.get(
            "class_name"
        )
    )

    return {
        "predicted_class":
            normalize_damage_class(
                predicted_class
            ),

        "confidence":
            confidence_percentage(
                phase1.get(
                    "confidence"
                )
            ),

        "severity":
            damage_severity(
                predicted_class
            ),
    }


# ============================================================
# OVERALL DECISION
# ============================================================

def build_overall_status(
    damage,
    document,
):
    damage_severity_value = damage.get(
        "severity",
        "Unknown",
    )

    risk_status = document.get(
        "risk_status",
        "Unknown",
    )

    review_flags = document.get(
        "review_flags",
        []
    )

    if (
        review_flags
        or
        risk_status in {
            "Incomplete",
            "Review Required",
        }
    ):
        return "Manual Review Recommended"

    if damage_severity_value == "High":
        return "Manual Review Recommended"

    if (
        damage_severity_value == "Normal"
        and
        risk_status == "Ready for Review"
    ):
        return "Assessment Ready"

    return "Review Required"


def build_recommendation(
    damage,
    document,
):
    severity = damage.get(
        "severity",
        "Unknown",
    )

    risk_status = document.get(
        "risk_status",
        "Unknown",
    )

    flags = document.get(
        "review_flags",
        []
    )

    if flags:
        return (
            "Resolve the document review items before "
            "final valuation or approval."
        )

    if risk_status in {
        "Incomplete",
        "Review Required",
    }:
        return (
            "Complete manual document verification before "
            "final valuation or approval."
        )

    if severity == "High":
        return (
            "Vehicle damage has been detected. Consider "
            "repair severity and its impact on market value "
            "before final valuation."
        )

    if severity == "Normal":
        return (
            "No damage category requiring attention was "
            "detected. Proceed with standard assessment."
        )

    return (
        "Additional review is recommended before a final decision."
    )


# ============================================================
# SUMMARY
# ============================================================

def build_summary(
    vehicle,
    damage,
    document,
):
    registration = (
        vehicle.get(
            "registration_number"
        )
        or
        "registration not available"
    )

    manufacturer = (
        vehicle.get(
            "manufacturer"
        )
        or
        ""
    )

    model = (
        vehicle.get(
            "model"
        )
        or
        ""
    )

    vehicle_name = " ".join(
        value
        for value in [
            manufacturer,
            model,
        ]
        if value
    ).strip()

    if not vehicle_name:
        vehicle_name = "the vehicle"

    return (
        f"Assessment generated for {vehicle_name} "
        f"({registration}). Phase 1 classified the vehicle as "
        f"'{damage.get('predicted_class', 'Not available')}'. "
        f"Phase 2 document completeness is "
        f"{document.get('completeness_score', 0)}% with status "
        f"'{document.get('risk_status', 'Unknown')}'."
    )


# ============================================================
# FINAL REPORT
# ============================================================

def generate_report(
    phase1_response,
    phase2_response,
):
    """
    Generate the business-facing Phase 4 report.

    IMPORTANT:
    raw_phase1, raw_phase2, OCR text and debug responses are
    intentionally NOT returned in this report.
    """

    phase1 = safe_dict(
        phase1_response
    )

    phase2 = safe_dict(
        phase2_response
    )

    damage = build_damage_assessment(
        phase1
    )

    document = build_document_assessment(
        phase2
    )

    vehicle = build_vehicle_information(
        phase2
    )

    identifiers = build_identifiers(
        phase2
    )

    document_fields = build_document_fields(
        phase2
    )

    overall_status = build_overall_status(
        damage,
        document,
    )

    recommendation = build_recommendation(
        damage,
        document,
    )

    summary = build_summary(
        vehicle,
        damage,
        document,
    )

    return {
        "report_type":
            "Used Car Assessment Report",

        "generated_at":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "overall_status":
            overall_status,

        "recommendation":
            recommendation,

        "summary":
            summary,

        "vehicle_information":
            vehicle,

        "identifiers":
            identifiers,

        "damage_assessment":
            damage,

        "document_assessment":
            document,

        "document_fields":
            document_fields,
    }


# ============================================================
# HUMAN-READABLE REPORT
# ============================================================

def report_to_text(
    report
):
    report = safe_dict(
        report
    )

    vehicle = safe_dict(
        report.get(
            "vehicle_information"
        )
    )

    identifiers = safe_dict(
        report.get(
            "identifiers"
        )
    )

    damage = safe_dict(
        report.get(
            "damage_assessment"
        )
    )

    document = safe_dict(
        report.get(
            "document_assessment"
        )
    )

    lines = [

        "AXIS USED CAR ASSESSMENT REPORT",
        "=" * 36,
        "",

        f"Overall Status: "
        f"{report.get('overall_status', 'Unknown')}",

        f"Recommendation: "
        f"{report.get('recommendation', 'Review required.')}",

        "",

        "VEHICLE INFORMATION",
        "-" * 20,

        f"Registration Number: "
        f"{vehicle.get('registration_number') or 'Not detected'}",

        f"Owner Name: "
        f"{vehicle.get('owner_name') or 'Not detected'}",

        f"Manufacturer: "
        f"{vehicle.get('manufacturer') or 'Not detected'}",

        f"Model: "
        f"{vehicle.get('model') or 'Not detected'}",

        f"Fuel Type: "
        f"{vehicle.get('fuel_type') or 'Not detected'}",

        f"Manufacturing Date: "
        f"{vehicle.get('manufacturing_date') or 'Not detected'}",

        "",

        "IDENTIFIERS",
        "-" * 11,

        f"Chassis Number: "
        f"{identifiers.get('chassis_number') or 'Not detected'}",

        f"Engine Number: "
        f"{identifiers.get('engine_number') or 'Not detected'}",

        "",

        "PHASE 1 — DAMAGE ASSESSMENT",
        "-" * 28,

        f"Predicted Condition: "
        f"{damage.get('predicted_class') or 'Not available'}",

        (
            f"Model Confidence: "
            f"{damage.get('confidence')}%"
            if damage.get("confidence") is not None
            else
            "Model Confidence: Not available"
        ),

        f"Severity: "
        f"{damage.get('severity', 'Unknown')}",

        "",

        "PHASE 2 — DOCUMENT ASSESSMENT",
        "-" * 30,

        f"Document Type: "
        f"{document.get('document_type', 'Unknown')}",

        f"Completeness: "
        f"{document.get('completeness_score', 0)}%",

        f"Risk Status: "
        f"{document.get('risk_status', 'Unknown')}",
    ]

    missing = document.get(
        "missing_information",
        []
    )

    if missing:

        lines.extend([
            "",
            "Missing Information:",
        ])

        lines.extend(
            f"- {item}"
            for item in missing
        )

    flags = document.get(
        "review_flags",
        []
    )

    if flags:

        lines.extend([
            "",
            "Review Items:",
        ])

        lines.extend(
            f"- {item}"
            for item in flags
        )

    lines.extend([
        "",
        "SUMMARY",
        "-" * 7,
        report.get(
            "summary",
            ""
        ),
    ])

    return "\n".join(
        lines
    )


# ============================================================
# EXPORT HELPERS
# ============================================================

def save_report_json(
    report,
    output_path,
):
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return path


def save_report_text(
    report,
    output_path,
):
    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        report_to_text(
            report
        ),
        encoding="utf-8",
    )

    return path
