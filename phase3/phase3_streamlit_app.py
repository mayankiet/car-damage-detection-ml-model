
import json

import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Axis Market Reference & Valuation",
    page_icon="💰",
    layout="wide",
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2f3142;
        margin-bottom: .2rem;
    }

    .subtitle {
        color: #626775;
        font-size: 1rem;
        margin-bottom: 1.4rem;
    }

    .section-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2f3142;
        margin-top: 1.5rem;
        margin-bottom: .5rem;
    }

    .card {
        border: 1px solid #e3e6eb;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        background: #fafbfc;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">💰 Axis Market Reference & Valuation</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">Phase 3 — Used Vehicle Market Valuation</div>',
    unsafe_allow_html=True,
)

st.write(
    """
    Phase 3 estimates a vehicle's fair market value by matching it
    against market-reference records and applying transparent
    adjustments for age, mileage, ownership and detected damage.
    """
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Configuration")

api_url = st.sidebar.text_input(
    "Phase 3 FastAPI URL",
    "http://127.0.0.1:8003",
)

if st.sidebar.button(
    "🔌 Test Phase 3 Connection"
):

    try:

        response = requests.get(
            f"{api_url}/",
            timeout=10,
        )

        if response.status_code == 200:

            st.sidebar.success(
                "Phase 3 API is connected."
            )

        else:

            st.sidebar.error(
                f"API returned {response.status_code}"
            )

    except Exception as error:

        st.sidebar.error(
            f"Connection failed: {error}"
        )


# ============================================================
# VEHICLE INPUTS
# ============================================================

st.markdown(
    '<div class="section-title">📋 Vehicle Information</div>',
    unsafe_allow_html=True,
)

c1, c2 = st.columns(
    2,
    gap="large",
)

with c1:

    manufacturer = st.text_input(
        "Manufacturer",
        "BMW INDIA PVT LTD",
    )

    model = st.text_input(
        "Model",
        "BMW X1 SDRIVE20D",
    )

    variant = st.text_input(
        "Variant",
        "",
    )

    manufacturing_date = st.text_input(
        "Manufacturing Date",
        "07/2019",
    )

    fuel_type = st.selectbox(
        "Fuel Type",
        [
            "Diesel",
            "Petrol",
            "CNG",
            "LPG",
            "Electric",
            "Hybrid",
        ],
    )


with c2:

    registration_number = st.text_input(
        "Registration Number",
        "",
    )

    city = st.text_input(
        "City",
        "Gurgaon",
    )

    mileage_km = st.number_input(
        "Current Mileage (km)",
        min_value=0,
        value=60000,
        step=1000,
    )

    owner_serial = st.selectbox(
        "Owner Serial",
        [
            "01",
            "02",
            "03",
            "04",
        ],
    )


# ============================================================
# DAMAGE INPUT
# ============================================================

st.markdown(
    '<div class="section-title">🔧 Phase 1 Damage Information</div>',
    unsafe_allow_html=True,
)

d1, d2 = st.columns(
    2,
    gap="large",
)

with d1:

    damage_class = st.selectbox(
        "Damage Classification",
        [
            "Front Normal",
            "Front Breakage",
            "Front Crushed",
            "Rear Normal",
            "Rear Breakage",
            "Rear Crushed",
        ],
    )

with d2:

    damage_confidence = st.number_input(
        "Damage Confidence (%)",
        min_value=0.0,
        max_value=100.0,
        value=90.0,
        step=1.0,
    )


# ============================================================
# BUTTON
# ============================================================

st.divider()

if st.button(
    "📊 Calculate Market Value",
    type="primary",
    use_container_width=True,
):

    payload = {

        "vehicle": {

            "registration_number":
                registration_number,

            "manufacturer":
                manufacturer,

            "model":
                model,

            "variant":
                variant,

            "manufacturing_date":
                manufacturing_date,

            "fuel_type":
                fuel_type,

            "city":
                city,

            "mileage_km":
                mileage_km,

            "owner_serial":
                owner_serial,
        },

        "damage": {

            "predicted_class":
                damage_class,

            "confidence":
                damage_confidence / 100,
        },
    }

    with st.spinner(
        "Matching market references and calculating value..."
    ):

        try:

            response = requests.post(
                f"{api_url}/valuate",
                json=payload,
                timeout=60,
            )

        except requests.exceptions.ConnectionError:

            st.error(
                """
                ❌ Cannot connect to Phase 3 FastAPI.

                Start it with:

                `uvicorn api:app --reload --port 8003`
                """
            )

            st.stop()

        except requests.exceptions.Timeout:

            st.error(
                "⏱️ Valuation request timed out."
            )

            st.stop()

        except Exception as error:

            st.error(
                f"❌ Request failed: {error}"
            )

            st.stop()


    try:

        result = response.json()

    except Exception:

        st.error(
            f"Phase 3 returned HTTP {response.status_code}"
        )

        st.code(
            response.text
        )

        st.stop()


    if not result.get(
        "success",
        False,
    ):

        st.error(
            result.get(
                "message",
                "No valuation could be generated.",
            )
        )

        st.stop()


    # ========================================================
    # RESULT
    # ========================================================

    st.success(
        "✅ Market valuation completed"
    )

    st.markdown(
        '<div class="section-title">💰 Valuation Result</div>',
        unsafe_allow_html=True,
    )

    reference_value = result.get(
        "reference_market_value_inr",
        0,
    )

    fair_value = result.get(
        "estimated_fair_value_inr",
        0,
    )

    confidence = result.get(
        "valuation_confidence_percent",
        0,
    )


    r1, r2, r3 = st.columns(3)

    r1.metric(
        "Reference Market Value",
        f"₹{reference_value:,.0f}",
    )

    r2.metric(
        "Estimated Fair Value",
        f"₹{fair_value:,.0f}",
    )

    r3.metric(
        "Valuation Confidence",
        f"{confidence}%",
    )


    # ========================================================
    # MARKET RANGE
    # ========================================================

    value_range = result.get(
        "valuation_range_inr",
        {},
    )

    st.markdown(
        "### 📈 Market Reference Range"
    )

    low = value_range.get(
        "low"
    )

    high = value_range.get(
        "high"
    )

    if low is not None and high is not None:

        st.info(
            f"Reference range: "
            f"**₹{low:,.0f} — ₹{high:,.0f}**"
        )


    # ========================================================
    # ADJUSTMENTS
    # ========================================================

    st.markdown(
        "### 🧮 Valuation Adjustments"
    )

    adjustments = result.get(
        "adjustments",
        {},
    )

    adjustment_names = [
        ("Age", "age"),
        ("Mileage", "mileage"),
        ("Ownership", "ownership"),
        ("Damage", "damage"),
    ]

    for label, key in adjustment_names:

        item = adjustments.get(
            key,
            {},
        )

        percentage = item.get(
            "percentage",
            0,
        )

        amount = item.get(
            "amount_inr",
            0,
        )

        st.write(
            f"**{label}:** "
            f"{percentage:+.2f}%  |  "
            f"₹{amount:+,.0f}"
        )


    # ========================================================
    # COMPARABLE VEHICLES
    # ========================================================

    st.markdown(
        "### 🚘 Comparable Market Records"
    )

    st.caption(
        f"{result.get('comparables_used', 0)} "
        "reference records were used."
    )

    for item in result.get(
        "comparables",
        [],
    ):

        st.write(
            f"**{item.get('brand', '')} "
            f"{item.get('model', '')} "
            f"{item.get('variant', '')}** | "
            f"{item.get('year', '')} | "
            f"{item.get('fuel', '')} | "
            f"{item.get('city', '')} | "
            f"₹{item.get('median_price_inr', 0):,.0f}"
        )


    # ========================================================
    # METHOD / DISCLAIMER
    # ========================================================

    st.markdown(
        "### 🧠 Valuation Method"
    )

    st.info(
        result.get(
            "valuation_method",
            "Market-reference valuation.",
        )
    )

    st.caption(
        "Reference values in the prototype dataset are illustrative "
        "market-reference records and should not be treated as verified "
        "transaction prices."
    )
