import base64
import json
from io import BytesIO

import requests
import streamlit as st



# ============================================================
# PROFESSIONAL PDF REPORT HELPERS
# ============================================================

def _money(value):
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "Not available"


def build_pdf_report(report):
    """
    Create the final business-facing PDF.
    Technical API responses, OCR dumps and debugging information
    are intentionally excluded.
    """

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle,
    )
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        PageBreak,
    )

    report = report if isinstance(report, dict) else {}

    vehicle = report.get("vehicle_information") or {}
    identifiers = report.get("identifiers") or {}
    damage = report.get("damage_assessment") or {}
    document = report.get("document_assessment") or {}
    document_fields = report.get("document_fields") or {}
    valuation = report.get("valuation") or {}

    # Backward compatibility with older Phase 4 output.
    if not document_fields:
        raw_phase2 = report.get("raw_phase2") or {}
        document_fields = raw_phase2.get("extracted_fields") or {}

    if not vehicle and document_fields:
        vehicle = {
            "registration_number": document_fields.get("registration_number"),
            "owner_name": document_fields.get("owner_name"),
            "manufacturer": document_fields.get("manufacturer"),
            "model": document_fields.get("model"),
            "fuel_type": document_fields.get("fuel_type"),
            "manufacturing_date": document_fields.get("manufacturing_date"),
            "colour": document_fields.get("colour"),
            "vehicle_class": document_fields.get("vehicle_class"),
            "body_type": document_fields.get("body_type"),
            "purpose": document_fields.get("purpose"),
        }

    if not identifiers and document_fields:
        identifiers = {
            "chassis_number": document_fields.get("chassis_number"),
            "engine_number": document_fields.get("engine_number"),
        }

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "ATitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#20232d"),
        spaceAfter=3 * mm,
    )

    subtitle = ParagraphStyle(
        "ASubtitle",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#626775"),
        spaceAfter=6 * mm,
    )

    h1 = ParagraphStyle(
        "AH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#20232d"),
        spaceBefore=4 * mm,
        spaceAfter=3 * mm,
    )

    h2 = ParagraphStyle(
        "AH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#2f3142"),
        spaceBefore=3 * mm,
        spaceAfter=2 * mm,
    )

    body = ParagraphStyle(
        "ABody",
        parent=styles["BodyText"],
        fontSize=8.8,
        leading=12.2,
        textColor=colors.HexColor("#343741"),
        spaceAfter=2 * mm,
    )

    small = ParagraphStyle(
        "ASmall",
        parent=body,
        fontSize=7.8,
        leading=10.4,
    )

    bold = ParagraphStyle(
        "ABold",
        parent=small,
        fontName="Helvetica-Bold",
    )

    story = []

    registration = (
        vehicle.get("registration_number")
        or "Not detected"
    )

    vehicle_name = (
        f"{vehicle.get('manufacturer') or ''} "
        f"{vehicle.get('model') or ''}"
    ).strip() or "Vehicle"

    story.append(
        Paragraph(
            "Axis Used Car Assessment Report",
            title,
        )
    )

    story.append(
        Paragraph(
            "Integrated vehicle condition, document and market valuation assessment",
            subtitle,
        )
    )

    overview = Table(
        [
            [
                Paragraph("<b>Registration</b>", small),
                Paragraph(str(registration), bold),
                Paragraph("<b>Overall Status</b>", small),
                Paragraph(
                    str(
                        report.get(
                            "overall_status",
                            "Review Required",
                        )
                    ),
                    bold,
                ),
            ],
            [
                Paragraph("<b>Vehicle</b>", small),
                Paragraph(vehicle_name, bold),
                Paragraph("<b>Document Status</b>", small),
                Paragraph(
                    str(
                        document.get(
                            "risk_status",
                            "Unknown",
                        )
                    ),
                    bold,
                ),
            ],
        ],
        colWidths=[32 * mm, 58 * mm, 34 * mm, 56 * mm],
    )

    overview.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(overview)

    # ========================================================
    # VEHICLE PROFILE
    # ========================================================

    story.append(
        Paragraph(
            "1. Vehicle Profile",
            h1,
        )
    )

    profile_fields = [
        ("Registration Number", "registration_number"),
        ("Owner Name", "owner_name"),
        ("Manufacturer", "manufacturer"),
        ("Model", "model"),
        ("Fuel Type", "fuel_type"),
        ("Manufacturing Date", "manufacturing_date"),
        ("Registration Date", "registration_date"),
        ("Registration Validity", "registration_validity"),
        ("Colour", "colour"),
        ("Vehicle Class", "vehicle_class"),
        ("Body Type", "body_type"),
        ("Purpose", "purpose"),
    ]

    profile_rows = []

    for label, key in profile_fields:
        profile_rows.append(
            [
                Paragraph(f"<b>{label}</b>", small),
                Paragraph(
                    str(
                        document_fields.get(key)
                        or vehicle.get(key)
                        or "Not detected"
                    ),
                    small,
                ),
            ]
        )

    profile_table = Table(
        profile_rows,
        colWidths=[50 * mm, 130 * mm],
    )

    profile_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(profile_table)

    # ========================================================
    # IDENTIFIERS
    # ========================================================

    story.append(
        Paragraph(
            "2. Vehicle Identifiers",
            h1,
        )
    )

    identifier_table = Table(
        [
            [
                Paragraph("<b>Chassis Number</b>", small),
                Paragraph(
                    str(
                        identifiers.get("chassis_number")
                        or "Not detected"
                    ),
                    small,
                ),
            ],
            [
                Paragraph("<b>Engine Number</b>", small),
                Paragraph(
                    str(
                        identifiers.get("engine_number")
                        or "Not detected"
                    ),
                    small,
                ),
            ],
        ],
        colWidths=[50 * mm, 130 * mm],
    )

    identifier_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(identifier_table)

    # ========================================================
    # DAMAGE
    # ========================================================

    story.append(
        Paragraph(
            "3. Damage Assessment",
            h1,
        )
    )

    confidence = damage.get("confidence")

    damage_table = Table(
        [
            [
                Paragraph("<b>Predicted Condition</b>", small),
                Paragraph(
                    str(
                        damage.get(
                            "predicted_class",
                            "Not available",
                        )
                    ),
                    small,
                ),
            ],
            [
                Paragraph("<b>Model Confidence</b>", small),
                Paragraph(
                    (
                        f"{confidence:.2f}%"
                        if isinstance(
                            confidence,
                            (int, float),
                        )
                        else "Not available"
                    ),
                    small,
                ),
            ],
            [
                Paragraph("<b>Severity</b>", small),
                Paragraph(
                    str(
                        damage.get(
                            "severity",
                            "Unknown",
                        )
                    ),
                    small,
                ),
            ],
        ],
        colWidths=[50 * mm, 130 * mm],
    )

    damage_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(damage_table)

    # ========================================================
    # DOCUMENT
    # ========================================================

    story.append(
        Paragraph(
            "4. Document Assessment",
            h1,
        )
    )

    document_table = Table(
        [
            [
                Paragraph("<b>Document Type</b>", small),
                Paragraph(
                    str(
                        document.get(
                            "document_type",
                            "Unknown",
                        )
                    ),
                    small,
                ),
            ],
            [
                Paragraph("<b>Completeness</b>", small),
                Paragraph(
                    f"{document.get('completeness_score', 0)}%",
                    small,
                ),
            ],
            [
                Paragraph("<b>Risk Status</b>", small),
                Paragraph(
                    str(
                        document.get(
                            "risk_status",
                            "Unknown",
                        )
                    ),
                    small,
                ),
            ],
        ],
        colWidths=[50 * mm, 130 * mm],
    )

    document_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story.append(document_table)

    story.append(
        Paragraph(
            "Extracted Information",
            h2,
        )
    )

    fields_order = [
        ("Registration Number", "registration_number"),
        ("Purpose", "purpose"),
        ("Manufacturing Date", "manufacturing_date"),
        ("Fuel Type", "fuel_type"),
        ("Body Type", "body_type"),
        ("Chassis Number", "chassis_number"),
        ("Model", "model"),
        ("Registration Validity", "registration_validity"),
        ("Unladen Weight", "unladen_weight"),
        ("Seat Capacity", "seat_capacity"),
        ("Number Of Cylinders", "number_of_cylinders"),
        ("Rlw", "rlw"),
        ("Address", "address"),
        ("Owner Name", "owner_name"),
        ("Registration Date", "registration_date"),
        ("Colour", "colour"),
        ("Vehicle Class", "vehicle_class"),
        ("Manufacturer", "manufacturer"),
        ("Engine Number", "engine_number"),
        ("Tax Paid Up To", "tax_paid_up_to"),
        ("Hypothecated To", "hypothecated_to"),
        ("Cubic Capacity", "cubic_capacity"),
        ("Standing Capacity", "standing_capacity"),
        ("Wheel Base", "wheel_base"),
        ("Owner Serial", "owner_serial"),
        ("Issuing Authority", "issuing_authority"),
    ]

    field_rows = [
        [
            Paragraph("<b>Field</b>", small),
            Paragraph("<b>Value</b>", small),
        ]
    ]

    for label, key in fields_order:
        value = document_fields.get(key)
        field_rows.append(
            [
                Paragraph(label, small),
                Paragraph(
                    str(value)
                    if value
                    else "Not detected",
                    small,
                ),
            ]
        )

    field_table = Table(
        field_rows,
        colWidths=[60 * mm, 120 * mm],
        repeatRows=1,
    )

    field_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    story.append(field_table)

    missing = document.get(
        "missing_information",
        []
    ) or []

    review_flags = document.get(
        "review_flags",
        []
    ) or []

    story.append(
        Paragraph(
            "Document Review",
            h2,
        )
    )

    story.append(
        Paragraph(
            "<b>Missing Information:</b> "
            + (
                ", ".join(
                    str(x)
                    for x in missing
                )
                if missing
                else "None"
            ),
            body,
        )
    )

    story.append(
        Paragraph(
            "<b>Review Items:</b> "
            + (
                "; ".join(
                    str(x)
                    for x in review_flags
                )
                if review_flags
                else "None"
            ),
            body,
        )
    )

    # ========================================================
    # VALUATION
    # ========================================================

    story.append(PageBreak())

    story.append(
        Paragraph(
            "5. Market Valuation",
            h1,
        )
    )

    if valuation.get("success"):

        story.append(
            Table(
                [
                    [
                        Paragraph("<b>Reference Market Value</b>", small),
                        Paragraph(
                            _money(
                                valuation.get(
                                    "reference_market_value_inr"
                                )
                            ),
                            small,
                        ),
                    ],
                    [
                        Paragraph("<b>Estimated Fair Value</b>", small),
                        Paragraph(
                            _money(
                                valuation.get(
                                    "estimated_fair_value_inr"
                                )
                            ),
                            bold,
                        ),
                    ],
                    [
                        Paragraph("<b>Valuation Confidence</b>", small),
                        Paragraph(
                            f"{valuation.get('valuation_confidence_percent', 0)}%",
                            small,
                        ),
                    ],
                    [
                        Paragraph("<b>Comparable Records Used</b>", small),
                        Paragraph(
                            str(
                                valuation.get(
                                    "comparables_used",
                                    0,
                                )
                            ),
                            small,
                        ),
                    ],
                ],
                colWidths=[58 * mm, 122 * mm],
            )
        )

        value_range = valuation.get(
            "valuation_range_inr",
            {}
        ) or {}

        if (
            value_range.get("low") is not None
            and
            value_range.get("high") is not None
        ):
            story.append(
                Paragraph(
                    f"<b>Reference Market Range:</b> "
                    f"{_money(value_range['low'])} - "
                    f"{_money(value_range['high'])}",
                    body,
                )
            )

        story.append(
            Paragraph(
                "Valuation Adjustments",
                h2,
            )
        )

        adjustment_rows = [
            [
                Paragraph("<b>Adjustment</b>", small),
                Paragraph("<b>Impact</b>", small),
                Paragraph("<b>Amount</b>", small),
            ]
        ]

        adjustments = valuation.get(
            "adjustments",
            {}
        ) or {}

        for label, key in [
            ("Age", "age"),
            ("Mileage", "mileage"),
            ("Ownership", "ownership"),
            ("Damage", "damage"),
        ]:

            item = adjustments.get(
                key,
                {}
            ) or {}

            adjustment_rows.append(
                [
                    Paragraph(label, small),
                    Paragraph(
                        f"{item.get('percentage', 0):+.2f}%",
                        small,
                    ),
                    Paragraph(
                        _money(
                            item.get(
                                "amount_inr",
                                0,
                            )
                        ),
                        small,
                    ),
                ]
            )

        adjustment_table = Table(
            adjustment_rows,
            colWidths=[55 * mm, 55 * mm, 70 * mm],
        )

        adjustment_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        story.append(
            adjustment_table
        )

        comparables = valuation.get(
            "comparables",
            []
        ) or []

        if comparables:

            story.append(
                Paragraph(
                    "Market Comparables",
                    h2,
                )
            )

            comp_rows = [
                [
                    Paragraph("<b>Model</b>", small),
                    Paragraph("<b>Year</b>", small),
                    Paragraph("<b>Fuel</b>", small),
                    Paragraph("<b>City</b>", small),
                    Paragraph("<b>Median</b>", small),
                ]
            ]

            for item in comparables[:10]:

                comp_rows.append(
                    [
                        Paragraph(
                            (
                                f"{item.get('model', '')} "
                                f"{item.get('variant', '')}"
                            ).strip(),
                            small,
                        ),
                        Paragraph(
                            str(item.get("year", "")),
                            small,
                        ),
                        Paragraph(
                            str(item.get("fuel", "")),
                            small,
                        ),
                        Paragraph(
                            str(item.get("city", "")),
                            small,
                        ),
                        Paragraph(
                            _money(
                                item.get(
                                    "median_price_inr",
                                    0,
                                )
                            ),
                            small,
                        ),
                    ]
                )

            comp_table = Table(
                comp_rows,
                colWidths=[
                    57 * mm,
                    22 * mm,
                    25 * mm,
                    30 * mm,
                    46 * mm,
                ],
                repeatRows=1,
            )

            comp_table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 3),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )

            story.append(
                comp_table
            )

    else:

        story.append(
            Paragraph(
                str(
                    valuation.get(
                        "message",
                        "No market valuation was generated.",
                    )
                ),
                body,
            )
        )

    # ========================================================
    # FINAL DECISION
    # ========================================================

    story.append(
        Paragraph(
            "6. Final Assessment",
            h1,
        )
    )

    story.append(
        Paragraph(
            f"<b>Overall Status:</b> "
            f"{report.get('overall_status', 'Review Required')}",
            body,
        )
    )

    story.append(
        Paragraph(
            f"<b>Recommendation:</b> "
            f"{report.get('recommendation', 'Additional review is recommended.')}",
            body,
        )
    )

    story.append(
        Paragraph(
            f"<b>Summary:</b> "
            f"{report.get('summary', 'Assessment summary unavailable.')}",
            body,
        )
    )

    output = BytesIO()

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(
            15 * mm,
            9 * mm,
            "Axis Used Car Assessment",
        )
        canvas.drawRightString(
            195 * mm,
            9 * mm,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    pdf = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title="Axis Used Car Assessment Report",
        author="Axis Used Car Assessment",
    )

    pdf.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    return output.getvalue()


def show_pdf(pdf_bytes):
    encoded = base64.b64encode(
        pdf_bytes
    ).decode("utf-8")

    st.markdown(
        f"""
        <iframe
            src="data:application/pdf;base64,{encoded}"
            width="100%"
            height="850"
            style="border:1px solid #e1e4e8;border-radius:12px;"
        ></iframe>
        """,
        unsafe_allow_html=True,
    )

st.set_page_config(
    page_title="Axis Used Car Assessment",
    page_icon="🚗",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.6rem;
        font-weight: 700;
        color: #2f3142;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #606473;
        margin-bottom: 1.2rem;
    }
    .section-title {
        font-size: 1.9rem;
        font-weight: 700;
        color: #2f3142;
        margin-top: 1.6rem;
        margin-bottom: 0.5rem;
    }
    .section-note {
        color: #666a78;
        margin-bottom: 1rem;
    }
    .phase-card {
        border: 1px solid #e2e5ea;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        background: #fafbfc;
        margin: 0.6rem 0 1rem 0;
    }
    .phase-label {
        font-size: .78rem;
        font-weight: 700;
        color: #747887;
        text-transform: uppercase;
        letter-spacing: .05em;
    }
    .phase-name {
        font-size: 1.3rem;
        font-weight: 700;
        color: #2f3142;
    }
    .phase-desc {
        color: #666a78;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PHASE1_API = "http://127.0.0.1:8000"
PHASE2_API = "http://127.0.0.1:8001"
PHASE4_API = "http://127.0.0.1:8003"


def get_json(response):
    try:
        return response.json()
    except Exception:
        return {
            "success": False,
            "error": response.text,
            "error_type": "InvalidJSONResponse",
            "http_status": response.status_code,
        }


def render_phase2(result):
    completeness = result.get("completeness_score", 0)
    risk_status = result.get("risk_status", "Unknown")
    document_type = result.get("document_type", "Unknown")
    fields = result.get("extracted_fields", {}) or {}

    st.markdown("## 📊 Document Assessment")
    c1, c2, c3 = st.columns(3)
    c1.metric("Completeness", f"{completeness}%")
    c2.metric("Risk Status", risk_status)
    c3.metric("Document Type", document_type)

    st.markdown("## 📌 Extracted Information")

    field_order = [
        ("Registration Number", "registration_number"),
        ("Purpose", "purpose"),
        ("Manufacturing Date", "manufacturing_date"),
        ("Fuel Type", "fuel_type"),
        ("Body Type", "body_type"),
        ("Chassis Number", "chassis_number"),
        ("Model", "model"),
        ("Registration Validity", "registration_validity"),
        ("Unladen Weight", "unladen_weight"),
        ("Seat Capacity", "seat_capacity"),
        ("Number Of Cylinders", "number_of_cylinders"),
        ("Rlw", "rlw"),
        ("Address", "address"),
        ("Owner Name", "owner_name"),
        ("Registration Date", "registration_date"),
        ("Colour", "colour"),
        ("Vehicle Class", "vehicle_class"),
        ("Manufacturer", "manufacturer"),
        ("Engine Number", "engine_number"),
        ("Tax Paid Up To", "tax_paid_up_to"),
        ("Hypothecated To", "hypothecated_to"),
        ("Cubic Capacity", "cubic_capacity"),
        ("Standing Capacity", "standing_capacity"),
        ("Wheel Base", "wheel_base"),
        ("Owner Serial", "owner_serial"),
        ("Issuing Authority", "issuing_authority"),
    ]

    for start in range(0, len(field_order), 2):
        row = field_order[start:start + 2]
        left, right = st.columns(2)

        for idx, (label, key) in enumerate(row):
            with (left if idx == 0 else right):
                value = fields.get(key)
                st.text_input(
                    label,
                    value=str(value) if value else "Not detected",
                    disabled=True,
                    key=f"phase2_{key}",
                )

    st.markdown("## 📝 AI-Assisted Summary")
    st.info(result.get("summary", "No summary available."))

    st.markdown("## ⚠️ Missing Information")
    missing = result.get("missing_information", []) or []
    if missing:
        for item in missing:
            st.warning(f"Missing: {item}")
    else:
        st.success("All important fields were detected.")

    st.markdown("## 🚩 Review Flags")
    flags = result.get("review_flags", []) or []
    if flags:
        for flag in flags:
            st.error(flag)
    else:
        st.success("No obvious review flags detected.")

    st.markdown("## 💡 Assessment")
    if document_type == "RC / Registration Certificate":
        if completeness >= 75:
            st.success(
                f"The system successfully identified the document as "
                f"**{document_type}** and extracted most of the expected information."
            )
        elif completeness >= 50:
            st.warning(
                f"The document was identified as **{document_type}**, but some "
                "important information could not be confidently extracted. "
                "Manual review is recommended."
            )
        else:
            st.error(
                f"The document was identified as **{document_type}**, but the "
                "extraction confidence is low. Manual verification is recommended."
            )
    else:
        st.info(f"Document identified as **{document_type}**.")

    with st.expander("📄 View Extracted OCR Text"):
        st.text(result.get("text_preview", "No OCR text returned."))

    with st.expander("🔧 View JSON Response"):
        st.code(
            json.dumps(result, indent=2),
            language="json",
        )


st.markdown(
    '<div class="main-title">🚗 Axis Used Car Assessment</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">Phase 4 — Combined Vehicle Assessment & Report Generation</div>',
    unsafe_allow_html=True,
)

st.write(
    "Analyze Phase 1 and Phase 2 independently, inspect their FastAPI "
    "responses, and then generate a combined assessment."
)

st.sidebar.title("⚙️ Configuration")

phase1_url = st.sidebar.text_input(
    "Phase 1 FastAPI URL",
    PHASE1_API,
)

phase2_url = st.sidebar.text_input(
    "Phase 2 FastAPI URL",
    PHASE2_API,
)

phase4_url = st.sidebar.text_input(
    "Phase 4 FastAPI URL",
    PHASE4_API,
)

# ============================================================
# PHASE 1
# ============================================================

st.markdown(
    '<div class="section-title">🔧 Phase 1 — Damage Detection</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="phase-card">
        <div class="phase-label">Phase 1</div>
        <div class="phase-name">🚗 Vehicle Damage Image</div>
        <div class="phase-desc">
            Upload a car image and send it directly to the Phase 1
            FastAPI damage classification service.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

damage_image = st.file_uploader(
    "Upload vehicle image",
    type=["jpg", "jpeg", "png"],
    key="damage_image",
)

if damage_image:

    st.image(
        damage_image,
        caption="Uploaded Vehicle Damage Image",
        width=700,
    )

    if st.button(
        "🔍 Analyze Phase 1",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Running Phase 1 damage detection..."
        ):

            try:

                response = requests.post(
                    f"{phase1_url}/predict",
                    files={
                        "file": (
                            damage_image.name,
                            damage_image.getvalue(),
                            damage_image.type
                            or "application/octet-stream",
                        )
                    },
                    timeout=120,
                )

                phase1_result = get_json(
                    response
                )

                st.session_state[
                    "phase1_result"
                ] = phase1_result

                st.session_state[
                    "phase1_status"
                ] = response.status_code

            except requests.exceptions.ConnectionError as error:

                st.session_state[
                    "phase1_result"
                ] = {
                    "success": False,
                    "error": str(error),
                    "error_type": "ConnectionError",
                }

                st.session_state[
                    "phase1_status"
                ] = None

            except requests.exceptions.Timeout as error:

                st.session_state[
                    "phase1_result"
                ] = {
                    "success": False,
                    "error": str(error),
                    "error_type": "Timeout",
                }

                st.session_state[
                    "phase1_status"
                ] = None


if st.session_state.get(
    "phase1_result"
):

    st.divider()

    status = st.session_state.get(
        "phase1_status"
    )

    result = st.session_state[
        "phase1_result"
    ]

    if status == 200 and result.get(
        "success",
        True,
    ):

        st.success(
            "✅ Phase 1 analysis completed"
        )

        predicted = result.get(
            "predicted_class",
            result.get(
                "class_name",
                "Not available",
            ),
        )

        confidence = result.get(
            "confidence"
        )

        c1, c2 = st.columns(2)

        with c1:
            st.metric(
                "Predicted Class",
                predicted or "Not available",
            )

        with c2:

            if confidence is not None:
                try:
                    confidence_value = float(
                        confidence
                    )

                    pct = (
                        confidence_value * 100
                        if confidence_value <= 1
                        else confidence_value
                    )

                    pct = max(
                        0,
                        min(
                            100,
                            pct,
                        ),
                    )

                    st.metric(
                        "Confidence",
                        f"{pct:.2f}%",
                    )

                    st.progress(
                        pct / 100
                    )

                except Exception:

                    st.metric(
                        "Confidence",
                        str(confidence),
                    )

            else:

                st.metric(
                    "Confidence",
                    "Not returned",
                )

    else:

        st.error(
            f"❌ Phase 1 API returned HTTP {status}"
            if status is not None
            else "❌ Phase 1 request failed"
        )

        st.warning(
            "The detailed FastAPI debugger response is shown below."
        )

    st.markdown(
        "### 🔌 Phase 1 FastAPI Response"
    )

    st.code(
        json.dumps(
            result,
            indent=2,
        ),
        language="json",
    )


# ============================================================
# PHASE 2
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">📄 Phase 2 — Document Intelligence</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="phase-card">
        <div class="phase-label">Phase 2</div>
        <div class="phase-name">📄 RC / Insurance Document</div>
        <div class="phase-desc">
            Upload the document and analyze it using the existing
            Phase 2 Gemini-powered FastAPI service.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

document = st.file_uploader(
    "Upload RC / insurance document",
    type=[
        "pdf",
        "docx",
        "txt",
        "jpg",
        "jpeg",
        "png",
        "webp",
    ],
    key="document",
)

if document:

    st.info(
        f"Selected document: **{document.name}**"
    )

    if document.type.startswith(
        "image/"
    ):

        st.image(
            document,
            caption="Uploaded Vehicle Document",
            width=700,
        )

    if st.button(
        "🔍 Analyze Phase 2 Document",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Running Phase 2 document analysis..."
        ):

            try:

                response = requests.post(
                    f"{phase2_url}/analyze",
                    files={
                        "file": (
                            document.name,
                            document.getvalue(),
                            document.type
                            or "application/octet-stream",
                        )
                    },
                    timeout=240,
                )

                phase2_result = get_json(
                    response
                )

                st.session_state[
                    "phase2_result"
                ] = phase2_result

                st.session_state[
                    "phase2_status"
                ] = response.status_code

            except Exception as error:

                st.session_state[
                    "phase2_result"
                ] = {
                    "success": False,
                    "error": str(error),
                    "error_type": type(error).__name__,
                }

                st.session_state[
                    "phase2_status"
                ] = None


if st.session_state.get(
    "phase2_result"
):

    st.divider()

    status = st.session_state.get(
        "phase2_status"
    )

    phase2_result = st.session_state[
        "phase2_result"
    ]

    if status == 200:

        st.success(
            "✅ Phase 2 analysis completed"
        )

        render_phase2(
            phase2_result
        )

    else:

        st.error(
            f"❌ Phase 2 API returned HTTP {status}"
        )

        st.code(
            json.dumps(
                phase2_result,
                indent=2,
            ),
            language="json",
        )



# ============================================================
# PHASE 3
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">💰 Phase 3 — Market Valuation</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="section-note">
    Use the vehicle information from Phase 2 and the damage
    classification from Phase 1 to calculate an estimated market value.
    </div>
    """,
    unsafe_allow_html=True,
)

# Optional valuation inputs. These are separate from the existing
# Phase 1 and Phase 2 UI and do not alter either section.
valuation_col1, valuation_col2, valuation_col3 = st.columns(
    3,
    gap="large",
)

with valuation_col1:

    valuation_city = st.text_input(
        "Valuation City",
        "Gurgaon",
        key="valuation_city",
    )

with valuation_col2:

    valuation_mileage = st.number_input(
        "Current Mileage (km)",
        min_value=0,
        value=60000,
        step=1000,
        key="valuation_mileage",
    )

with valuation_col3:

    valuation_owner = st.text_input(
        "Owner Serial",
        "",
        key="valuation_owner",
    )


if st.button(
    "💰 Calculate Phase 3 Valuation",
    type="primary",
    use_container_width=True,
    key="calculate_phase3",
):

    phase2_for_valuation = st.session_state.get(
        "phase2_result"
    ) or {}

    phase1_for_valuation = st.session_state.get(
        "phase1_result"
    ) or {}

    if not phase2_for_valuation:

        st.error(
            "❌ Please analyze the Phase 2 document first."
        )

    else:

        extracted = phase2_for_valuation.get(
            "extracted_fields",
            {}
        ) or {}

        phase2_vehicle = {
            "registration_number":
                extracted.get("registration_number"),

            "manufacturer":
                extracted.get("manufacturer"),

            "model":
                extracted.get("model"),

            "variant":
                extracted.get("variant"),

            "manufacturing_date":
                extracted.get("manufacturing_date"),

            "registration_date":
                extracted.get("registration_date"),

            "fuel_type":
                extracted.get("fuel_type"),

            "owner_serial":
                valuation_owner
                or
                extracted.get("owner_serial"),

            "city":
                valuation_city,

            "mileage_km":
                valuation_mileage,
        }

        phase1_damage = {
            "predicted_class":
                phase1_for_valuation.get(
                    "predicted_class"
                )
                or
                phase1_for_valuation.get(
                    "class_name"
                ),

            "confidence":
                phase1_for_valuation.get(
                    "confidence"
                ),
        }

        if not phase1_damage["predicted_class"]:

            st.warning(
                "Phase 1 damage classification is not available. "
                "Valuation will proceed without a damage adjustment."
            )

        with st.spinner(
            "Calculating market valuation..."
        ):

            try:

                valuation_response = requests.post(

                    "http://127.0.0.1:8002/valuate",

                    json={
                        "vehicle": phase2_vehicle,
                        "damage": phase1_damage,
                    },

                    timeout=90,
                )

                valuation_result = get_json(
                    valuation_response
                )

                st.session_state[
                    "phase3_result"
                ] = valuation_result

                st.session_state[
                    "phase3_status"
                ] = valuation_response.status_code

            except requests.exceptions.ConnectionError:

                st.session_state[
                    "phase3_result"
                ] = {
                    "success": False,
                    "error":
                        "Cannot connect to Phase 3 FastAPI on port 8002.",
                    "error_type":
                        "ConnectionError",
                }

                st.session_state[
                    "phase3_status"
                ] = None

            except requests.exceptions.Timeout:

                st.session_state[
                    "phase3_result"
                ] = {
                    "success": False,
                    "error":
                        "Phase 3 valuation request timed out.",
                    "error_type":
                        "Timeout",
                }

                st.session_state[
                    "phase3_status"
                ] = None

            except Exception as error:

                st.session_state[
                    "phase3_result"
                ] = {
                    "success": False,
                    "error": str(error),
                    "error_type":
                        type(error).__name__,
                }

                st.session_state[
                    "phase3_status"
                ] = None


# ------------------------------------------------------------
# Phase 3 Result
# ------------------------------------------------------------

if st.session_state.get(
    "phase3_result"
):

    st.divider()

    st.markdown(
        '<div class="section-title">💰 Phase 3 — Valuation Result</div>',
        unsafe_allow_html=True,
    )

    phase3 = st.session_state[
        "phase3_result"
    ]

    phase3_status = st.session_state.get(
        "phase3_status"
    )

    if (
        phase3_status != 200
        or
        not phase3.get(
            "success",
            False,
        )
    ):

        st.error(
            phase3.get(
                "message",
                phase3.get(
                    "error",
                    "Phase 3 valuation could not be generated.",
                ),
            )
        )

    else:

        st.success(
            "✅ Market valuation completed"
        )

        reference_value = phase3.get(
            "reference_market_value_inr",
            0,
        )

        fair_value = phase3.get(
            "estimated_fair_value_inr",
            0,
        )

        valuation_confidence = phase3.get(
            "valuation_confidence_percent",
            0,
        )

        result_col1, result_col2, result_col3 = st.columns(
            3,
            gap="large",
        )

        with result_col1:

            st.metric(
                "Reference Market Value",
                f"₹{reference_value:,.0f}",
            )

        with result_col2:

            st.metric(
                "Estimated Fair Value",
                f"₹{fair_value:,.0f}",
            )

        with result_col3:

            st.metric(
                "Valuation Confidence",
                f"{valuation_confidence}%",
            )

        value_range = phase3.get(
            "valuation_range_inr",
            {}
        ) or {}

        low = value_range.get(
            "low"
        )

        high = value_range.get(
            "high"
        )

        if (
            low is not None
            and
            high is not None
        ):

            st.info(
                f"Reference market range: "
                f"**₹{low:,.0f} — ₹{high:,.0f}**"
            )

        st.markdown(
            "### 🧮 Valuation Adjustments"
        )

        adjustments = phase3.get(
            "adjustments",
            {}
        ) or {}

        adjustment_rows = [
            ("Age", "age"),
            ("Mileage", "mileage"),
            ("Ownership", "ownership"),
            ("Damage", "damage"),
        ]

        for label, key in adjustment_rows:

            adjustment = adjustments.get(
                key,
                {}
            ) or {}

            st.write(
                f"**{label}:** "
                f"{adjustment.get('percentage', 0):+.2f}%"
                f"  |  "
                f"₹{adjustment.get('amount_inr', 0):+,.0f}"
            )

        comparables = phase3.get(
            "comparables",
            []
        ) or []

        if comparables:

            st.markdown(
                "### 🚘 Market Comparables"
            )

            st.caption(
                f"{phase3.get('comparables_used', len(comparables))} "
                "reference records used."
            )

            for comparable in comparables:

                st.write(
                    f"**{comparable.get('brand', '')} "
                    f"{comparable.get('model', '')} "
                    f"{comparable.get('variant', '')}**"
                    f" — {comparable.get('year', '')}"
                    f" — {comparable.get('fuel', '')}"
                    f" — {comparable.get('city', '')}"
                    f" — ₹{comparable.get('median_price_inr', 0):,.0f}"
                )


# ============================================================
# PHASE 4
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">🧠 Phase 4 — Combined Assessment</div>',
    unsafe_allow_html=True,
)

if (
    st.session_state.get("phase1_result")
    and st.session_state.get("phase2_result")
):

    if st.button(
        "📊 Generate Combined Assessment",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Combining Phase 1 + Phase 2..."
        ):

            try:

                response = requests.post(
                    f"{phase4_url}/generate-report",
                    files={
                        "damage_image": (
                            damage_image.name,
                            damage_image.getvalue(),
                            damage_image.type
                            or "application/octet-stream",
                        ),
                        "document": (
                            document.name,
                            document.getvalue(),
                            document.type
                            or "application/octet-stream",
                        ),
                    },
                    timeout=300,
                )

                result = get_json(
                    response
                )

                if response.status_code != 200:

                    st.error(
                        f"❌ Phase 4 API returned HTTP {response.status_code}"
                    )

                    st.code(
                        json.dumps(
                            result,
                            indent=2,
                        ),
                        language="json",
                    )

                else:

                    st.session_state[
                        "phase4_result"
                    ] = result

            except Exception as error:

                st.error(
                    f"❌ Phase 4 error: {error}"
                )

else:

    st.info(
        "Analyze Phase 1 and Phase 2 first to enable the combined assessment."
    )



if st.session_state.get(
    "phase4_result"
):

    report = st.session_state[
        "phase4_result"
    ]

    if isinstance(report, dict) and report.get("error"):

        st.error(
            report.get(
                "error",
                "Final assessment failed.",
            )
        )

    else:

        st.success(
            "✅ Combined assessment generated"
        )

        st.markdown(
            '<div class="section-title">📋 Final Assessment Report</div>',
            unsafe_allow_html=True,
        )

        st.info(
            "Your complete assessment is available as a professional PDF report."
        )

        # Generate only after the combined Phase 4 result exists.
        try:

            pdf_bytes = build_pdf_report(
                report
            )

            st.download_button(
                "⬇️ Download Combined PDF Report",
                data=pdf_bytes,
                file_name="axis_used_car_assessment_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            st.markdown(
                "### 👁️ View Report"
            )

            show_pdf(
                pdf_bytes
            )

        except Exception as error:
            import base64
            import json
            from io import BytesIO

            import requests
            import streamlit as st


            # ============================================================
            # PROFESSIONAL PDF REPORT HELPERS
            # ============================================================

            def _money(value):
                try:
                    return f"₹{float(value):,.0f}"
                except (TypeError, ValueError):
                    return "Not available"


            def build_pdf_report(report):
                """
                Create the final business-facing PDF.
                Technical API responses, OCR dumps and debugging information
                are intentionally excluded.
                """

                from reportlab.lib import colors
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import (
                    getSampleStyleSheet,
                    ParagraphStyle,
                )
                from reportlab.lib.units import mm
                from reportlab.platypus import (
                    SimpleDocTemplate,
                    Paragraph,
                    Spacer,
                    Table,
                    TableStyle,
                    PageBreak,
                )

                report = report if isinstance(report, dict) else {}

                vehicle = report.get("vehicle_information") or {}
                identifiers = report.get("identifiers") or {}
                damage = report.get("damage_assessment") or {}
                document = report.get("document_assessment") or {}
                document_fields = report.get("document_fields") or {}
                valuation = report.get("valuation") or {}

                # Backward compatibility with older Phase 4 output.
                if not document_fields:
                    raw_phase2 = report.get("raw_phase2") or {}
                    document_fields = raw_phase2.get("extracted_fields") or {}

                if not vehicle and document_fields:
                    vehicle = {
                        "registration_number": document_fields.get("registration_number"),
                        "owner_name": document_fields.get("owner_name"),
                        "manufacturer": document_fields.get("manufacturer"),
                        "model": document_fields.get("model"),
                        "fuel_type": document_fields.get("fuel_type"),
                        "manufacturing_date": document_fields.get("manufacturing_date"),
                        "colour": document_fields.get("colour"),
                        "vehicle_class": document_fields.get("vehicle_class"),
                        "body_type": document_fields.get("body_type"),
                        "purpose": document_fields.get("purpose"),
                    }

                if not identifiers and document_fields:
                    identifiers = {
                        "chassis_number": document_fields.get("chassis_number"),
                        "engine_number": document_fields.get("engine_number"),
                    }

                styles = getSampleStyleSheet()

                title = ParagraphStyle(
                    "ATitle",
                    parent=styles["Title"],
                    fontName="Helvetica-Bold",
                    fontSize=22,
                    leading=26,
                    textColor=colors.HexColor("#20232d"),
                    spaceAfter=3 * mm,
                )

                subtitle = ParagraphStyle(
                    "ASubtitle",
                    parent=styles["Normal"],
                    fontSize=9.5,
                    leading=13,
                    textColor=colors.HexColor("#626775"),
                    spaceAfter=6 * mm,
                )

                h1 = ParagraphStyle(
                    "AH1",
                    parent=styles["Heading1"],
                    fontName="Helvetica-Bold",
                    fontSize=14,
                    leading=18,
                    textColor=colors.HexColor("#20232d"),
                    spaceBefore=4 * mm,
                    spaceAfter=3 * mm,
                )

                h2 = ParagraphStyle(
                    "AH2",
                    parent=styles["Heading2"],
                    fontName="Helvetica-Bold",
                    fontSize=10.5,
                    leading=14,
                    textColor=colors.HexColor("#2f3142"),
                    spaceBefore=3 * mm,
                    spaceAfter=2 * mm,
                )

                body = ParagraphStyle(
                    "ABody",
                    parent=styles["BodyText"],
                    fontSize=8.8,
                    leading=12.2,
                    textColor=colors.HexColor("#343741"),
                    spaceAfter=2 * mm,
                )

                small = ParagraphStyle(
                    "ASmall",
                    parent=body,
                    fontSize=7.8,
                    leading=10.4,
                )

                bold = ParagraphStyle(
                    "ABold",
                    parent=small,
                    fontName="Helvetica-Bold",
                )

                story = []

                registration = (
                        vehicle.get("registration_number")
                        or "Not detected"
                )

                vehicle_name = (
                                   f"{vehicle.get('manufacturer') or ''} "
                                   f"{vehicle.get('model') or ''}"
                               ).strip() or "Vehicle"

                story.append(
                    Paragraph(
                        "Axis Used Car Assessment Report",
                        title,
                    )
                )

                story.append(
                    Paragraph(
                        "Integrated vehicle condition, document and market valuation assessment",
                        subtitle,
                    )
                )

                overview = Table(
                    [
                        [
                            Paragraph("<b>Registration</b>", small),
                            Paragraph(str(registration), bold),
                            Paragraph("<b>Overall Status</b>", small),
                            Paragraph(
                                str(
                                    report.get(
                                        "overall_status",
                                        "Review Required",
                                    )
                                ),
                                bold,
                            ),
                        ],
                        [
                            Paragraph("<b>Vehicle</b>", small),
                            Paragraph(vehicle_name, bold),
                            Paragraph("<b>Document Status</b>", small),
                            Paragraph(
                                str(
                                    document.get(
                                        "risk_status",
                                        "Unknown",
                                    )
                                ),
                                bold,
                            ),
                        ],
                    ],
                    colWidths=[32 * mm, 58 * mm, 34 * mm, 56 * mm],
                )

                overview.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                            ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )

                story.append(overview)

                # ========================================================
                # VEHICLE PROFILE
                # ========================================================

                story.append(
                    Paragraph(
                        "1. Vehicle Profile",
                        h1,
                    )
                )

                profile_fields = [
                    ("Registration Number", "registration_number"),
                    ("Owner Name", "owner_name"),
                    ("Manufacturer", "manufacturer"),
                    ("Model", "model"),
                    ("Fuel Type", "fuel_type"),
                    ("Manufacturing Date", "manufacturing_date"),
                    ("Registration Date", "registration_date"),
                    ("Registration Validity", "registration_validity"),
                    ("Colour", "colour"),
                    ("Vehicle Class", "vehicle_class"),
                    ("Body Type", "body_type"),
                    ("Purpose", "purpose"),
                ]

                profile_rows = []

                for label, key in profile_fields:
                    profile_rows.append(
                        [
                            Paragraph(f"<b>{label}</b>", small),
                            Paragraph(
                                str(
                                    document_fields.get(key)
                                    or vehicle.get(key)
                                    or "Not detected"
                                ),
                                small,
                            ),
                        ]
                    )

                profile_table = Table(
                    profile_rows,
                    colWidths=[50 * mm, 130 * mm],
                )

                profile_table.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 4),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )

                story.append(profile_table)

                # ========================================================
                # IDENTIFIERS
                # ========================================================

                story.append(
                    Paragraph(
                        "2. Vehicle Identifiers",
                        h1,
                    )
                )

                identifier_table = Table(
                    [
                        [
                            Paragraph("<b>Chassis Number</b>", small),
                            Paragraph(
                                str(
                                    identifiers.get("chassis_number")
                                    or "Not detected"
                                ),
                                small,
                            ),
                        ],
                        [
                            Paragraph("<b>Engine Number</b>", small),
                            Paragraph(
                                str(
                                    identifiers.get("engine_number")
                                    or "Not detected"
                                ),
                                small,
                            ),
                        ],
                    ],
                    colWidths=[50 * mm, 130 * mm],
                )

                identifier_table.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                            ("LEFTPADDING", (0, 0), (-1, -1), 4),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )

                story.append(identifier_table)

                # ========================================================
                # DAMAGE
                # ========================================================

                story.append(
                    Paragraph(
                        "3. Damage Assessment",
                        h1,
                    )
                )

                confidence = damage.get("confidence")

                damage_table = Table(
                    [
                        [
                            Paragraph("<b>Predicted Condition</b>", small),
                            Paragraph(
                                str(
                                    damage.get(
                                        "predicted_class",
                                        "Not available",
                                    )
                                ),
                                small,
                            ),
                        ],
                        [
                            Paragraph("<b>Model Confidence</b>", small),
                            Paragraph(
                                (
                                    f"{confidence:.2f}%"
                                    if isinstance(
                                        confidence,
                                        (int, float),
                                    )
                                    else "Not available"
                                ),
                                small,
                            ),
                        ],
                        [
                            Paragraph("<b>Severity</b>", small),
                            Paragraph(
                                str(
                                    damage.get(
                                        "severity",
                                        "Unknown",
                                    )
                                ),
                                small,
                            ),
                        ],
                    ],
                    colWidths=[50 * mm, 130 * mm],
                )

                damage_table.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                            ("LEFTPADDING", (0, 0), (-1, -1), 4),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )

                story.append(damage_table)

                # ========================================================
                # DOCUMENT
                # ========================================================

                story.append(
                    Paragraph(
                        "4. Document Assessment",
                        h1,
                    )
                )

                document_table = Table(
                    [
                        [
                            Paragraph("<b>Document Type</b>", small),
                            Paragraph(
                                str(
                                    document.get(
                                        "document_type",
                                        "Unknown",
                                    )
                                ),
                                small,
                            ),
                        ],
                        [
                            Paragraph("<b>Completeness</b>", small),
                            Paragraph(
                                f"{document.get('completeness_score', 0)}%",
                                small,
                            ),
                        ],
                        [
                            Paragraph("<b>Risk Status</b>", small),
                            Paragraph(
                                str(
                                    document.get(
                                        "risk_status",
                                        "Unknown",
                                    )
                                ),
                                small,
                            ),
                        ],
                    ],
                    colWidths=[50 * mm, 130 * mm],
                )

                document_table.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
                            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                            ("LEFTPADDING", (0, 0), (-1, -1), 4),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )

                story.append(document_table)

                story.append(
                    Paragraph(
                        "Extracted Information",
                        h2,
                    )
                )

                fields_order = [
                    ("Registration Number", "registration_number"),
                    ("Purpose", "purpose"),
                    ("Manufacturing Date", "manufacturing_date"),
                    ("Fuel Type", "fuel_type"),
                    ("Body Type", "body_type"),
                    ("Chassis Number", "chassis_number"),
                    ("Model", "model"),
                    ("Registration Validity", "registration_validity"),
                    ("Unladen Weight", "unladen_weight"),
                    ("Seat Capacity", "seat_capacity"),
                    ("Number Of Cylinders", "number_of_cylinders"),
                    ("Rlw", "rlw"),
                    ("Address", "address"),
                    ("Owner Name", "owner_name"),
                    ("Registration Date", "registration_date"),
                    ("Colour", "colour"),
                    ("Vehicle Class", "vehicle_class"),
                    ("Manufacturer", "manufacturer"),
                    ("Engine Number", "engine_number"),
                    ("Tax Paid Up To", "tax_paid_up_to"),
                    ("Hypothecated To", "hypothecated_to"),
                    ("Cubic Capacity", "cubic_capacity"),
                    ("Standing Capacity", "standing_capacity"),
                    ("Wheel Base", "wheel_base"),
                    ("Owner Serial", "owner_serial"),
                    ("Issuing Authority", "issuing_authority"),
                ]

                field_rows = [
                    [
                        Paragraph("<b>Field</b>", small),
                        Paragraph("<b>Value</b>", small),
                    ]
                ]

                for label, key in fields_order:
                    value = document_fields.get(key)
                    field_rows.append(
                        [
                            Paragraph(label, small),
                            Paragraph(
                                str(value)
                                if value
                                else "Not detected",
                                small,
                            ),
                        ]
                    )

                field_table = Table(
                    field_rows,
                    colWidths=[60 * mm, 120 * mm],
                    repeatRows=1,
                )

                field_table.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 3),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    )
                )

                story.append(field_table)

                missing = document.get(
                    "missing_information",
                    []
                ) or []

                review_flags = document.get(
                    "review_flags",
                    []
                ) or []

                story.append(
                    Paragraph(
                        "Document Review",
                        h2,
                    )
                )

                story.append(
                    Paragraph(
                        "<b>Missing Information:</b> "
                        + (
                            ", ".join(
                                str(x)
                                for x in missing
                            )
                            if missing
                            else "None"
                        ),
                        body,
                    )
                )

                story.append(
                    Paragraph(
                        "<b>Review Items:</b> "
                        + (
                            "; ".join(
                                str(x)
                                for x in review_flags
                            )
                            if review_flags
                            else "None"
                        ),
                        body,
                    )
                )

                # ========================================================
                # VALUATION
                # ========================================================

                story.append(PageBreak())

                story.append(
                    Paragraph(
                        "5. Market Valuation",
                        h1,
                    )
                )

                if valuation.get("success"):

                    story.append(
                        Table(
                            [
                                [
                                    Paragraph("<b>Reference Market Value</b>", small),
                                    Paragraph(
                                        _money(
                                            valuation.get(
                                                "reference_market_value_inr"
                                            )
                                        ),
                                        small,
                                    ),
                                ],
                                [
                                    Paragraph("<b>Estimated Fair Value</b>", small),
                                    Paragraph(
                                        _money(
                                            valuation.get(
                                                "estimated_fair_value_inr"
                                            )
                                        ),
                                        bold,
                                    ),
                                ],
                                [
                                    Paragraph("<b>Valuation Confidence</b>", small),
                                    Paragraph(
                                        f"{valuation.get('valuation_confidence_percent', 0)}%",
                                        small,
                                    ),
                                ],
                                [
                                    Paragraph("<b>Comparable Records Used</b>", small),
                                    Paragraph(
                                        str(
                                            valuation.get(
                                                "comparables_used",
                                                0,
                                            )
                                        ),
                                        small,
                                    ),
                                ],
                            ],
                            colWidths=[58 * mm, 122 * mm],
                        )
                    )

                    value_range = valuation.get(
                        "valuation_range_inr",
                        {}
                    ) or {}

                    if (
                            value_range.get("low") is not None
                            and
                            value_range.get("high") is not None
                    ):
                        story.append(
                            Paragraph(
                                f"<b>Reference Market Range:</b> "
                                f"{_money(value_range['low'])} - "
                                f"{_money(value_range['high'])}",
                                body,
                            )
                        )

                    story.append(
                        Paragraph(
                            "Valuation Adjustments",
                            h2,
                        )
                    )

                    adjustment_rows = [
                        [
                            Paragraph("<b>Adjustment</b>", small),
                            Paragraph("<b>Impact</b>", small),
                            Paragraph("<b>Amount</b>", small),
                        ]
                    ]

                    adjustments = valuation.get(
                        "adjustments",
                        {}
                    ) or {}

                    for label, key in [
                        ("Age", "age"),
                        ("Mileage", "mileage"),
                        ("Ownership", "ownership"),
                        ("Damage", "damage"),
                    ]:
                        item = adjustments.get(
                            key,
                            {}
                        ) or {}

                        adjustment_rows.append(
                            [
                                Paragraph(label, small),
                                Paragraph(
                                    f"{item.get('percentage', 0):+.2f}%",
                                    small,
                                ),
                                Paragraph(
                                    _money(
                                        item.get(
                                            "amount_inr",
                                            0,
                                        )
                                    ),
                                    small,
                                ),
                            ]
                        )

                    adjustment_table = Table(
                        adjustment_rows,
                        colWidths=[55 * mm, 55 * mm, 70 * mm],
                    )

                    adjustment_table.setStyle(
                        TableStyle(
                            [
                                ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                                ("TOPPADDING", (0, 0), (-1, -1), 3),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ]
                        )
                    )

                    story.append(
                        adjustment_table
                    )

                    comparables = valuation.get(
                        "comparables",
                        []
                    ) or []

                    if comparables:

                        story.append(
                            Paragraph(
                                "Market Comparables",
                                h2,
                            )
                        )

                        comp_rows = [
                            [
                                Paragraph("<b>Model</b>", small),
                                Paragraph("<b>Year</b>", small),
                                Paragraph("<b>Fuel</b>", small),
                                Paragraph("<b>City</b>", small),
                                Paragraph("<b>Median</b>", small),
                            ]
                        ]

                        for item in comparables[:10]:
                            comp_rows.append(
                                [
                                    Paragraph(
                                        (
                                            f"{item.get('model', '')} "
                                            f"{item.get('variant', '')}"
                                        ).strip(),
                                        small,
                                    ),
                                    Paragraph(
                                        str(item.get("year", "")),
                                        small,
                                    ),
                                    Paragraph(
                                        str(item.get("fuel", "")),
                                        small,
                                    ),
                                    Paragraph(
                                        str(item.get("city", "")),
                                        small,
                                    ),
                                    Paragraph(
                                        _money(
                                            item.get(
                                                "median_price_inr",
                                                0,
                                            )
                                        ),
                                        small,
                                    ),
                                ]
                            )

                        comp_table = Table(
                            comp_rows,
                            colWidths=[
                                57 * mm,
                                22 * mm,
                                25 * mm,
                                30 * mm,
                                46 * mm,
                            ],
                            repeatRows=1,
                        )

                        comp_table.setStyle(
                            TableStyle(
                                [
                                    ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
                                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                                ]
                            )
                        )

                        story.append(
                            comp_table
                        )

                else:

                    story.append(
                        Paragraph(
                            str(
                                valuation.get(
                                    "message",
                                    "No market valuation was generated.",
                                )
                            ),
                            body,
                        )
                    )

                # ========================================================
                # FINAL DECISION
                # ========================================================

                story.append(
                    Paragraph(
                        "6. Final Assessment",
                        h1,
                    )
                )

                story.append(
                    Paragraph(
                        f"<b>Overall Status:</b> "
                        f"{report.get('overall_status', 'Review Required')}",
                        body,
                    )
                )

                story.append(
                    Paragraph(
                        f"<b>Recommendation:</b> "
                        f"{report.get('recommendation', 'Additional review is recommended.')}",
                        body,
                    )
                )

                story.append(
                    Paragraph(
                        f"<b>Summary:</b> "
                        f"{report.get('summary', 'Assessment summary unavailable.')}",
                        body,
                    )
                )

                output = BytesIO()

                def footer(canvas, doc):
                    canvas.saveState()
                    canvas.setFont("Helvetica", 8)
                    canvas.setFillColor(colors.grey)
                    canvas.drawString(
                        15 * mm,
                        9 * mm,
                        "Axis Used Car Assessment",
                    )
                    canvas.drawRightString(
                        195 * mm,
                        9 * mm,
                        f"Page {doc.page}",
                    )
                    canvas.restoreState()

                pdf = SimpleDocTemplate(
                    output,
                    pagesize=A4,
                    leftMargin=15 * mm,
                    rightMargin=15 * mm,
                    topMargin=14 * mm,
                    bottomMargin=16 * mm,
                    title="Axis Used Car Assessment Report",
                    author="Axis Used Car Assessment",
                )

                pdf.build(
                    story,
                    onFirstPage=footer,
                    onLaterPages=footer,
                )

                return output.getvalue()


            def show_pdf(pdf_bytes):
                encoded = base64.b64encode(
                    pdf_bytes
                ).decode("utf-8")

                st.markdown(
                    f"""
                    <iframe
                        src="data:application/pdf;base64,{encoded}"
                        width="100%"
                        height="850"
                        style="border:1px solid #e1e4e8;border-radius:12px;"
                    ></iframe>
                    """,
                    unsafe_allow_html=True,
                )


            st.set_page_config(
                page_title="Axis Used Car Assessment",
                page_icon="🚗",
                layout="wide",
            )

            st.markdown(
                """
                <style>
                .main-title {
                    font-size: 2.6rem;
                    font-weight: 700;
                    color: #2f3142;
                }
                .subtitle {
                    font-size: 1.05rem;
                    color: #606473;
                    margin-bottom: 1.2rem;
                }
                .section-title {
                    font-size: 1.9rem;
                    font-weight: 700;
                    color: #2f3142;
                    margin-top: 1.6rem;
                    margin-bottom: 0.5rem;
                }
                .section-note {
                    color: #666a78;
                    margin-bottom: 1rem;
                }
                .phase-card {
                    border: 1px solid #e2e5ea;
                    border-radius: 14px;
                    padding: 1rem 1.2rem;
                    background: #fafbfc;
                    margin: 0.6rem 0 1rem 0;
                }
                .phase-label {
                    font-size: .78rem;
                    font-weight: 700;
                    color: #747887;
                    text-transform: uppercase;
                    letter-spacing: .05em;
                }
                .phase-name {
                    font-size: 1.3rem;
                    font-weight: 700;
                    color: #2f3142;
                }
                .phase-desc {
                    color: #666a78;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            PHASE1_API = "http://127.0.0.1:8000"
            PHASE2_API = "http://127.0.0.1:8001"
            PHASE4_API = "http://127.0.0.1:8003"


            def get_json(response):
                try:
                    return response.json()
                except Exception:
                    return {
                        "success": False,
                        "error": response.text,
                        "error_type": "InvalidJSONResponse",
                        "http_status": response.status_code,
                    }


            def render_phase2(result):
                completeness = result.get("completeness_score", 0)
                risk_status = result.get("risk_status", "Unknown")
                document_type = result.get("document_type", "Unknown")
                fields = result.get("extracted_fields", {}) or {}

                st.markdown("## 📊 Document Assessment")
                c1, c2, c3 = st.columns(3)
                c1.metric("Completeness", f"{completeness}%")
                c2.metric("Risk Status", risk_status)
                c3.metric("Document Type", document_type)

                st.markdown("## 📌 Extracted Information")

                field_order = [
                    ("Registration Number", "registration_number"),
                    ("Purpose", "purpose"),
                    ("Manufacturing Date", "manufacturing_date"),
                    ("Fuel Type", "fuel_type"),
                    ("Body Type", "body_type"),
                    ("Chassis Number", "chassis_number"),
                    ("Model", "model"),
                    ("Registration Validity", "registration_validity"),
                    ("Unladen Weight", "unladen_weight"),
                    ("Seat Capacity", "seat_capacity"),
                    ("Number Of Cylinders", "number_of_cylinders"),
                    ("Rlw", "rlw"),
                    ("Address", "address"),
                    ("Owner Name", "owner_name"),
                    ("Registration Date", "registration_date"),
                    ("Colour", "colour"),
                    ("Vehicle Class", "vehicle_class"),
                    ("Manufacturer", "manufacturer"),
                    ("Engine Number", "engine_number"),
                    ("Tax Paid Up To", "tax_paid_up_to"),
                    ("Hypothecated To", "hypothecated_to"),
                    ("Cubic Capacity", "cubic_capacity"),
                    ("Standing Capacity", "standing_capacity"),
                    ("Wheel Base", "wheel_base"),
                    ("Owner Serial", "owner_serial"),
                    ("Issuing Authority", "issuing_authority"),
                ]

                for start in range(0, len(field_order), 2):
                    row = field_order[start:start + 2]
                    left, right = st.columns(2)

                    for idx, (label, key) in enumerate(row):
                        with (left if idx == 0 else right):
                            value = fields.get(key)
                            st.text_input(
                                label,
                                value=str(value) if value else "Not detected",
                                disabled=True,
                                key=f"phase2_{key}",
                            )

                st.markdown("## 📝 AI-Assisted Summary")
                st.info(result.get("summary", "No summary available."))

                st.markdown("## ⚠️ Missing Information")
                missing = result.get("missing_information", []) or []
                if missing:
                    for item in missing:
                        st.warning(f"Missing: {item}")
                else:
                    st.success("All important fields were detected.")

                st.markdown("## 🚩 Review Flags")
                flags = result.get("review_flags", []) or []
                if flags:
                    for flag in flags:
                        st.error(flag)
                else:
                    st.success("No obvious review flags detected.")

                st.markdown("## 💡 Assessment")
                if document_type == "RC / Registration Certificate":
                    if completeness >= 75:
                        st.success(
                            f"The system successfully identified the document as "
                            f"**{document_type}** and extracted most of the expected information."
                        )
                    elif completeness >= 50:
                        st.warning(
                            f"The document was identified as **{document_type}**, but some "
                            "important information could not be confidently extracted. "
                            "Manual review is recommended."
                        )
                    else:
                        st.error(
                            f"The document was identified as **{document_type}**, but the "
                            "extraction confidence is low. Manual verification is recommended."
                        )
                else:
                    st.info(f"Document identified as **{document_type}**.")

                with st.expander("📄 View Extracted OCR Text"):
                    st.text(result.get("text_preview", "No OCR text returned."))

                with st.expander("🔧 View JSON Response"):
                    st.code(
                        json.dumps(result, indent=2),
                        language="json",
                    )


            st.markdown(
                '<div class="main-title">🚗 Axis Used Car Assessment</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="subtitle">Phase 4 — Combined Vehicle Assessment & Report Generation</div>',
                unsafe_allow_html=True,
            )

            st.write(
                "Analyze Phase 1 and Phase 2 independently, inspect their FastAPI "
                "responses, and then generate a combined assessment."
            )

            st.sidebar.title("⚙️ Configuration")

            phase1_url = st.sidebar.text_input(
                "Phase 1 FastAPI URL",
                PHASE1_API,
            )

            phase2_url = st.sidebar.text_input(
                "Phase 2 FastAPI URL",
                PHASE2_API,
            )

            phase4_url = st.sidebar.text_input(
                "Phase 4 FastAPI URL",
                PHASE4_API,
            )

            # ============================================================
            # PHASE 1
            # ============================================================

            st.markdown(
                '<div class="section-title">🔧 Phase 1 — Damage Detection</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="phase-card">
                    <div class="phase-label">Phase 1</div>
                    <div class="phase-name">🚗 Vehicle Damage Image</div>
                    <div class="phase-desc">
                        Upload a car image and send it directly to the Phase 1
                        FastAPI damage classification service.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            damage_image = st.file_uploader(
                "Upload vehicle image",
                type=["jpg", "jpeg", "png"],
                key="damage_image",
            )

            if damage_image:

                st.image(
                    damage_image,
                    caption="Uploaded Vehicle Damage Image",
                    width=700,
                )

                if st.button(
                        "🔍 Analyze Phase 1",
                        type="primary",
                        use_container_width=True,
                ):

                    with st.spinner(
                            "Running Phase 1 damage detection..."
                    ):

                        try:

                            response = requests.post(
                                f"{phase1_url}/predict",
                                files={
                                    "file": (
                                        damage_image.name,
                                        damage_image.getvalue(),
                                        damage_image.type
                                        or "application/octet-stream",
                                    )
                                },
                                timeout=120,
                            )

                            phase1_result = get_json(
                                response
                            )

                            st.session_state[
                                "phase1_result"
                            ] = phase1_result

                            st.session_state[
                                "phase1_status"
                            ] = response.status_code

                        except requests.exceptions.ConnectionError as error:

                            st.session_state[
                                "phase1_result"
                            ] = {
                                "success": False,
                                "error": str(error),
                                "error_type": "ConnectionError",
                            }

                            st.session_state[
                                "phase1_status"
                            ] = None

                        except requests.exceptions.Timeout as error:

                            st.session_state[
                                "phase1_result"
                            ] = {
                                "success": False,
                                "error": str(error),
                                "error_type": "Timeout",
                            }

                            st.session_state[
                                "phase1_status"
                            ] = None

            if st.session_state.get(
                    "phase1_result"
            ):

                st.divider()

                status = st.session_state.get(
                    "phase1_status"
                )

                result = st.session_state[
                    "phase1_result"
                ]

                if status == 200 and result.get(
                        "success",
                        True,
                ):

                    st.success(
                        "✅ Phase 1 analysis completed"
                    )

                    predicted = result.get(
                        "predicted_class",
                        result.get(
                            "class_name",
                            "Not available",
                        ),
                    )

                    confidence = result.get(
                        "confidence"
                    )

                    c1, c2 = st.columns(2)

                    with c1:
                        st.metric(
                            "Predicted Class",
                            predicted or "Not available",
                        )

                    with c2:

                        if confidence is not None:
                            try:
                                confidence_value = float(
                                    confidence
                                )

                                pct = (
                                    confidence_value * 100
                                    if confidence_value <= 1
                                    else confidence_value
                                )

                                pct = max(
                                    0,
                                    min(
                                        100,
                                        pct,
                                    ),
                                )

                                st.metric(
                                    "Confidence",
                                    f"{pct:.2f}%",
                                )

                                st.progress(
                                    pct / 100
                                )

                            except Exception:

                                st.metric(
                                    "Confidence",
                                    str(confidence),
                                )

                        else:

                            st.metric(
                                "Confidence",
                                "Not returned",
                            )

                else:

                    st.error(
                        f"❌ Phase 1 API returned HTTP {status}"
                        if status is not None
                        else "❌ Phase 1 request failed"
                    )

                    st.warning(
                        "The detailed FastAPI debugger response is shown below."
                    )

                st.markdown(
                    "### 🔌 Phase 1 FastAPI Response"
                )

                st.code(
                    json.dumps(
                        result,
                        indent=2,
                    ),
                    language="json",
                )

            # ============================================================
            # PHASE 2
            # ============================================================

            st.divider()

            st.markdown(
                '<div class="section-title">📄 Phase 2 — Document Intelligence</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="phase-card">
                    <div class="phase-label">Phase 2</div>
                    <div class="phase-name">📄 RC / Insurance Document</div>
                    <div class="phase-desc">
                        Upload the document and analyze it using the existing
                        Phase 2 Gemini-powered FastAPI service.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            document = st.file_uploader(
                "Upload RC / insurance document",
                type=[
                    "pdf",
                    "docx",
                    "txt",
                    "jpg",
                    "jpeg",
                    "png",
                    "webp",
                ],
                key="document",
            )

            if document:

                st.info(
                    f"Selected document: **{document.name}**"
                )

                if document.type.startswith(
                        "image/"
                ):
                    st.image(
                        document,
                        caption="Uploaded Vehicle Document",
                        width=700,
                    )

                if st.button(
                        "🔍 Analyze Phase 2 Document",
                        type="primary",
                        use_container_width=True,
                ):

                    with st.spinner(
                            "Running Phase 2 document analysis..."
                    ):

                        try:

                            response = requests.post(
                                f"{phase2_url}/analyze",
                                files={
                                    "file": (
                                        document.name,
                                        document.getvalue(),
                                        document.type
                                        or "application/octet-stream",
                                    )
                                },
                                timeout=240,
                            )

                            phase2_result = get_json(
                                response
                            )

                            st.session_state[
                                "phase2_result"
                            ] = phase2_result

                            st.session_state[
                                "phase2_status"
                            ] = response.status_code

                        except Exception as error:

                            st.session_state[
                                "phase2_result"
                            ] = {
                                "success": False,
                                "error": str(error),
                                "error_type": type(error).__name__,
                            }

                            st.session_state[
                                "phase2_status"
                            ] = None

            if st.session_state.get(
                    "phase2_result"
            ):

                st.divider()

                status = st.session_state.get(
                    "phase2_status"
                )

                phase2_result = st.session_state[
                    "phase2_result"
                ]

                if status == 200:

                    st.success(
                        "✅ Phase 2 analysis completed"
                    )

                    render_phase2(
                        phase2_result
                    )

                else:

                    st.error(
                        f"❌ Phase 2 API returned HTTP {status}"
                    )

                    st.code(
                        json.dumps(
                            phase2_result,
                            indent=2,
                        ),
                        language="json",
                    )

            # ============================================================
            # PHASE 3
            # ============================================================

            st.divider()

            st.markdown(
                '<div class="section-title">💰 Phase 3 — Market Valuation</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="section-note">
                Use the vehicle information from Phase 2 and the damage
                classification from Phase 1 to calculate an estimated market value.
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Optional valuation inputs. These are separate from the existing
            # Phase 1 and Phase 2 UI and do not alter either section.
            valuation_col1, valuation_col2, valuation_col3 = st.columns(
                3,
                gap="large",
            )

            with valuation_col1:

                valuation_city = st.text_input(
                    "Valuation City",
                    "Gurgaon",
                    key="valuation_city",
                )

            with valuation_col2:

                valuation_mileage = st.number_input(
                    "Current Mileage (km)",
                    min_value=0,
                    value=60000,
                    step=1000,
                    key="valuation_mileage",
                )

            with valuation_col3:

                valuation_owner = st.text_input(
                    "Owner Serial",
                    "",
                    key="valuation_owner",
                )

            if st.button(
                    "💰 Calculate Phase 3 Valuation",
                    type="primary",
                    use_container_width=True,
                    key="calculate_phase3",
            ):

                phase2_for_valuation = st.session_state.get(
                    "phase2_result"
                ) or {}

                phase1_for_valuation = st.session_state.get(
                    "phase1_result"
                ) or {}

                if not phase2_for_valuation:

                    st.error(
                        "❌ Please analyze the Phase 2 document first."
                    )

                else:

                    extracted = phase2_for_valuation.get(
                        "extracted_fields",
                        {}
                    ) or {}

                    phase2_vehicle = {
                        "registration_number":
                            extracted.get("registration_number"),

                        "manufacturer":
                            extracted.get("manufacturer"),

                        "model":
                            extracted.get("model"),

                        "variant":
                            extracted.get("variant"),

                        "manufacturing_date":
                            extracted.get("manufacturing_date"),

                        "registration_date":
                            extracted.get("registration_date"),

                        "fuel_type":
                            extracted.get("fuel_type"),

                        "owner_serial":
                            valuation_owner
                            or
                            extracted.get("owner_serial"),

                        "city":
                            valuation_city,

                        "mileage_km":
                            valuation_mileage,
                    }

                    phase1_damage = {
                        "predicted_class":
                            phase1_for_valuation.get(
                                "predicted_class"
                            )
                            or
                            phase1_for_valuation.get(
                                "class_name"
                            ),

                        "confidence":
                            phase1_for_valuation.get(
                                "confidence"
                            ),
                    }

                    if not phase1_damage["predicted_class"]:
                        st.warning(
                            "Phase 1 damage classification is not available. "
                            "Valuation will proceed without a damage adjustment."
                        )

                    with st.spinner(
                            "Calculating market valuation..."
                    ):

                        try:

                            valuation_response = requests.post(

                                "http://127.0.0.1:8002/valuate",

                                json={
                                    "vehicle": phase2_vehicle,
                                    "damage": phase1_damage,
                                },

                                timeout=90,
                            )

                            valuation_result = get_json(
                                valuation_response
                            )

                            st.session_state[
                                "phase3_result"
                            ] = valuation_result

                            st.session_state[
                                "phase3_status"
                            ] = valuation_response.status_code

                        except requests.exceptions.ConnectionError:

                            st.session_state[
                                "phase3_result"
                            ] = {
                                "success": False,
                                "error":
                                    "Cannot connect to Phase 3 FastAPI on port 8002.",
                                "error_type":
                                    "ConnectionError",
                            }

                            st.session_state[
                                "phase3_status"
                            ] = None

                        except requests.exceptions.Timeout:

                            st.session_state[
                                "phase3_result"
                            ] = {
                                "success": False,
                                "error":
                                    "Phase 3 valuation request timed out.",
                                "error_type":
                                    "Timeout",
                            }

                            st.session_state[
                                "phase3_status"
                            ] = None

                        except Exception as error:

                            st.session_state[
                                "phase3_result"
                            ] = {
                                "success": False,
                                "error": str(error),
                                "error_type":
                                    type(error).__name__,
                            }

                            st.session_state[
                                "phase3_status"
                            ] = None

            # ------------------------------------------------------------
            # Phase 3 Result
            # ------------------------------------------------------------

            if st.session_state.get(
                    "phase3_result"
            ):

                st.divider()

                st.markdown(
                    '<div class="section-title">💰 Phase 3 — Valuation Result</div>',
                    unsafe_allow_html=True,
                )

                phase3 = st.session_state[
                    "phase3_result"
                ]

                phase3_status = st.session_state.get(
                    "phase3_status"
                )

                if (
                        phase3_status != 200
                        or
                        not phase3.get(
                            "success",
                            False,
                        )
                ):

                    st.error(
                        phase3.get(
                            "message",
                            phase3.get(
                                "error",
                                "Phase 3 valuation could not be generated.",
                            ),
                        )
                    )

                else:

                    st.success(
                        "✅ Market valuation completed"
                    )

                    reference_value = phase3.get(
                        "reference_market_value_inr",
                        0,
                    )

                    fair_value = phase3.get(
                        "estimated_fair_value_inr",
                        0,
                    )

                    valuation_confidence = phase3.get(
                        "valuation_confidence_percent",
                        0,
                    )

                    result_col1, result_col2, result_col3 = st.columns(
                        3,
                        gap="large",
                    )

                    with result_col1:

                        st.metric(
                            "Reference Market Value",
                            f"₹{reference_value:,.0f}",
                        )

                    with result_col2:

                        st.metric(
                            "Estimated Fair Value",
                            f"₹{fair_value:,.0f}",
                        )

                    with result_col3:

                        st.metric(
                            "Valuation Confidence",
                            f"{valuation_confidence}%",
                        )

                    value_range = phase3.get(
                        "valuation_range_inr",
                        {}
                    ) or {}

                    low = value_range.get(
                        "low"
                    )

                    high = value_range.get(
                        "high"
                    )

                    if (
                            low is not None
                            and
                            high is not None
                    ):
                        st.info(
                            f"Reference market range: "
                            f"**₹{low:,.0f} — ₹{high:,.0f}**"
                        )

                    st.markdown(
                        "### 🧮 Valuation Adjustments"
                    )

                    adjustments = phase3.get(
                        "adjustments",
                        {}
                    ) or {}

                    adjustment_rows = [
                        ("Age", "age"),
                        ("Mileage", "mileage"),
                        ("Ownership", "ownership"),
                        ("Damage", "damage"),
                    ]

                    for label, key in adjustment_rows:
                        adjustment = adjustments.get(
                            key,
                            {}
                        ) or {}

                        st.write(
                            f"**{label}:** "
                            f"{adjustment.get('percentage', 0):+.2f}%"
                            f"  |  "
                            f"₹{adjustment.get('amount_inr', 0):+,.0f}"
                        )

                    comparables = phase3.get(
                        "comparables",
                        []
                    ) or []

                    if comparables:

                        st.markdown(
                            "### 🚘 Market Comparables"
                        )

                        st.caption(
                            f"{phase3.get('comparables_used', len(comparables))} "
                            "reference records used."
                        )

                        for comparable in comparables:
                            st.write(
                                f"**{comparable.get('brand', '')} "
                                f"{comparable.get('model', '')} "
                                f"{comparable.get('variant', '')}**"
                                f" — {comparable.get('year', '')}"
                                f" — {comparable.get('fuel', '')}"
                                f" — {comparable.get('city', '')}"
                                f" — ₹{comparable.get('median_price_inr', 0):,.0f}"
                            )

            # ============================================================
            # PHASE 4
            # ============================================================

            st.divider()

            st.markdown(
                '<div class="section-title">🧠 Phase 4 — Combined Assessment</div>',
                unsafe_allow_html=True,
            )

            if (
                    st.session_state.get("phase1_result")
                    and st.session_state.get("phase2_result")
            ):

                if st.button(
                        "📊 Generate Combined Assessment",
                        type="primary",
                        use_container_width=True,
                ):

                    with st.spinner(
                            "Combining Phase 1 + Phase 2..."
                    ):

                        try:

                            response = requests.post(
                                f"{phase4_url}/generate-report",
                                files={
                                    "damage_image": (
                                        damage_image.name,
                                        damage_image.getvalue(),
                                        damage_image.type
                                        or "application/octet-stream",
                                    ),
                                    "document": (
                                        document.name,
                                        document.getvalue(),
                                        document.type
                                        or "application/octet-stream",
                                    ),
                                },
                                timeout=300,
                            )

                            result = get_json(
                                response
                            )

                            if response.status_code != 200:

                                st.error(
                                    f"❌ Phase 4 API returned HTTP {response.status_code}"
                                )

                                st.code(
                                    json.dumps(
                                        result,
                                        indent=2,
                                    ),
                                    language="json",
                                )

                            else:

                                st.session_state[
                                    "phase4_result"
                                ] = result

                        except Exception as error:

                            st.error(
                                f"❌ Phase 4 error: {error}"
                            )

            else:

                st.info(
                    "Analyze Phase 1 and Phase 2 first to enable the combined assessment."
                )

            if st.session_state.get(
                    "phase4_result"
            ):

                report = st.session_state[
                    "phase4_result"
                ]

                if isinstance(report, dict) and report.get("error"):

                    st.error(
                        report.get(
                            "error",
                            "Final assessment failed.",
                        )
                    )

                else:

                    st.success(
                        "✅ Combined assessment generated"
                    )

                    st.markdown(
                        '<div class="section-title">📋 Final Assessment Report</div>',
                        unsafe_allow_html=True,
                    )

                    st.info(
                        "Your complete assessment is available as a professional PDF report."
                    )

                    # Generate only after the combined Phase 4 result exists.
                    try:

                        pdf_bytes = build_pdf_report(
                            report
                        )

                        st.download_button(
                            "⬇️ Download Combined PDF Report",
                            data=pdf_bytes,
                            file_name="axis_used_car_assessment_report.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )

                        st.markdown(
                            "### 👁️ View Report"
                        )

                        show_pdf(
                            pdf_bytes
                        )

                    except Exception as error:

                        st.error(
                            f"❌ Could not generate the PDF report: {error}"
                        )

            st.divider()

            st.caption(
                "Axis Used Car Assessment — Phase 4 Hackathon Prototype"
            )

            st.error(
                f"❌ Could not generate the PDF report: {error}"
            )



st.divider()

st.caption(
    "Axis Used Car Assessment — Phase 4 Hackathon Prototype"
)
