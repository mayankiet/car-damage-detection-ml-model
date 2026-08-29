import json
import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Axis Document Intelligence",
    page_icon="📄",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "📄 Axis Document Intelligence"
)

st.subheader(
    "Phase 2 — Intelligent Document Processing"
)

st.write(
    """
Upload an RC, insurance, vehicle or claim document and the system
will automatically identify the document type, extract important
information, check completeness and highlight documents that
require further review.
"""
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "⚙️ Configuration"
)

api_url = st.sidebar.text_input(
    "FastAPI URL",
    "http://127.0.0.1:8000"
)


st.sidebar.markdown(
    """
### 📄 Supported Documents

**Vehicle Documents**
- Registration Certificate (RC)

**Insurance Documents**
- Insurance Policy
- Insurance Claim Form

**File Formats**
- PDF
- DOCX
- TXT
- JPG
- JPEG
- PNG
"""
)


# ============================================================
# CONNECTION CHECK
# ============================================================

if st.sidebar.button(
    "🔌 Test FastAPI Connection"
):

    try:

        response = requests.get(
            f"{api_url}/",
            timeout=10
        )

        if response.status_code == 200:

            st.sidebar.success(
                "FastAPI is connected."
            )

        else:

            st.sidebar.error(
                f"FastAPI returned {response.status_code}"
            )

    except Exception as error:

        st.sidebar.error(
            f"Connection failed: {error}"
        )


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "📤 Upload your document",

    type=[
        "pdf",
        "docx",
        "txt",
        "jpg",
        "jpeg",
        "png",
        "webp"
    ]
)


# ============================================================
# SHOW UPLOADED FILE
# ============================================================

if uploaded_file:

    st.info(
        f"Selected file: **{uploaded_file.name}**"
    )

    # --------------------------------------------------------
    # Preview image
    # --------------------------------------------------------

    if uploaded_file.type.startswith(
        "image/"
    ):

        st.image(
            uploaded_file,
            caption="Uploaded Document",
            width=600
        )


    # ========================================================
    # ANALYZE BUTTON
    # ========================================================

    if st.button(
        "🔍 Analyze Document",
        type="primary"
    ):

        with st.spinner(
            "Analyzing document... Please wait."
        ):

            try:

                # ------------------------------------------------
                # Send file to FastAPI
                # ------------------------------------------------

                response = requests.post(

                    f"{api_url}/analyze",

                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )
                    },

                    timeout=180
                )


                # ------------------------------------------------
                # Error response
                # ------------------------------------------------

                if response.status_code != 200:

                    st.error(
                        "❌ FastAPI returned an error."
                    )

                    st.code(
                        response.text
                    )

                else:

                    # ------------------------------------------------
                    # Parse JSON
                    # ------------------------------------------------

                    result = response.json()


                    st.success(
                        "✅ Document analysis completed"
                    )


                    # =================================================
                    # DOCUMENT ASSESSMENT
                    # =================================================

                    st.markdown(
                        "## 📊 Document Assessment"
                    )

                    col1, col2, col3 = st.columns(
                        3
                    )


                    with col1:

                        st.metric(
                            "Completeness",
                            f"{result.get('completeness_score', 0)}%"
                        )


                    with col2:

                        st.metric(
                            "Risk Status",
                            result.get(
                                "risk_status",
                                "Unknown"
                            )
                        )


                    with col3:

                        st.metric(
                            "Document Type",
                            result.get(
                                "document_type",
                                "Unknown"
                            )
                        )


                    # =================================================
                    # EXTRACTED INFORMATION
                    # =================================================

                    st.markdown(
                        "## 📌 Extracted Information"
                    )

                    fields = result.get(
                        "extracted_fields",
                        {}
                    )


                    if fields:

                        col1, col2 = st.columns(
                            2
                        )

                        field_items = list(
                            fields.items()
                        )


                        for index, (
                            field_name,
                            value
                        ) in enumerate(
                            field_items
                        ):

                            current_column = (
                                col1
                                if index % 2 == 0
                                else col2
                            )


                            with current_column:

                                readable_name = (
                                    field_name
                                    .replace(
                                        "_",
                                        " "
                                    )
                                    .title()
                                )


                                st.text_input(

                                    readable_name,

                                    value=(
                                        str(value)
                                        if value
                                        else "Not detected"
                                    ),

                                    disabled=True
                                )

                    else:

                        st.warning(
                            """
                            No structured fields were extracted.
                            The document may be unsupported or the
                            OCR could not read the document clearly.
                            """
                        )


                    # =================================================
                    # SUMMARY
                    # =================================================

                    st.markdown(
                        "## 📝 AI-Assisted Summary"
                    )

                    st.info(
                        result.get(
                            "summary",
                            "No summary available."
                        )
                    )


                    # =================================================
                    # MISSING INFORMATION
                    # =================================================

                    st.markdown(
                        "## ⚠️ Missing Information"
                    )

                    missing = result.get(
                        "missing_information",
                        []
                    )


                    if missing:

                        for item in missing:

                            st.warning(
                                f"Missing: {item}"
                            )

                    else:

                        if fields:

                            st.success(
                                "All important fields were detected."
                            )

                        else:

                            st.info(
                                "No structured fields are required for this document."
                            )


                    # =================================================
                    # REVIEW FLAGS
                    # =================================================

                    st.markdown(
                        "## 🚩 Review Flags"
                    )

                    flags = result.get(
                        "review_flags",
                        []
                    )


                    if flags:

                        for flag in flags:

                            st.error(
                                flag
                            )

                    else:

                        st.success(
                            "No obvious review flags detected."
                        )


                    # =================================================
                    # DOCUMENT STATUS EXPLANATION
                    # =================================================

                    st.markdown(
                        "## 💡 Assessment"
                    )

                    document_type = result.get(
                        "document_type",
                        "Unknown"
                    )

                    completeness = result.get(
                        "completeness_score",
                        0
                    )

                    risk_status = result.get(
                        "risk_status",
                        "Unknown"
                    )


                    if document_type == "General Document":

                        st.warning(
                            """
                            The uploaded file could not be confidently
                            identified as an RC, Insurance Policy,
                            Insurance Claim or Driving Licence.

                            Try uploading a clearer scan or photograph
                            of the actual document.
                            """
                        )

                    elif completeness >= 75:

                        st.success(
                            f"""
                            The system successfully identified the
                            document as **{document_type}** and extracted
                            most of the expected information.
                            """
                        )

                    elif completeness >= 50:

                        st.warning(
                            f"""
                            The document was identified as
                            **{document_type}**, but some important
                            information could not be confidently
                            extracted. Manual review is recommended.
                            """
                        )

                    else:

                        st.error(
                            f"""
                            The document was identified as
                            **{document_type}**, but the OCR/extraction
                            confidence is low. Manual verification is
                            recommended.
                            """
                        )


                    # =================================================
                    # RAW OCR TEXT
                    # =================================================

                    with st.expander(
                        "📄 View Extracted OCR Text"
                    ):

                        st.text(
                            result.get(
                                "text_preview",
                                "No text extracted."
                            )
                        )


                    # =================================================
                    # JSON RESPONSE
                    # =================================================

                    with st.expander(
                        "🔧 View JSON Response"
                    ):

                        st.code(

                            json.dumps(
                                result,
                                indent=2
                            ),

                            language="json"
                        )


            # ========================================================
            # CONNECTION ERROR
            # ========================================================

            except requests.exceptions.ConnectionError:

                st.error(
                    """
                    ❌ Cannot connect to FastAPI.

                    Please make sure the FastAPI server is running.

                    Run:

                    `uvicorn phase2.api:app --reload`
                    """
                )


            # ========================================================
            # TIMEOUT
            # ========================================================

            except requests.exceptions.Timeout:

                st.error(
                    """
                    ⏱️ The document analysis took too long.

                    This can happen with large PDFs or high-resolution
                    images. Try a smaller image or PDF.
                    """
                )


            # ========================================================
            # INVALID JSON
            # ========================================================

            except requests.exceptions.JSONDecodeError:

                st.error(
                    "FastAPI returned an invalid response."
                )

                st.code(
                    response.text
                )


            # ========================================================
            # GENERAL ERROR
            # ========================================================

            except Exception as error:

                st.error(
                    f"❌ Unexpected error: {error}"
                )


# ============================================================
# NO FILE
# ============================================================

else:

    st.info(
        """
        👆 Upload an RC, Insurance Policy,
        or Insurance Claim document to begin.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Axis Document Intelligence — Phase 2 Hackathon Prototype"
)