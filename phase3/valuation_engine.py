from __future__ import annotations

import csv
import re
from pathlib import Path
from statistics import median
from typing import Any, Optional


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CSV_CANDIDATES = [
    BASE_DIR / "market_reference.csv",
    BASE_DIR / "phase3_market_reference_multi_brand.csv",
    BASE_DIR / "phase3_market_reference.csv",
]


# ============================================================
# PROTOTYPE DAMAGE ADJUSTMENTS
# ============================================================
#
# These are business assumptions for the hackathon prototype.
# They are NOT claimed to be observed market statistics.
#

DAMAGE_ADJUSTMENTS = {
    "normal": 0.00,
    "breakage": -0.08,
    "crushed": -0.15,
}


# ============================================================
# BASIC HELPERS
# ============================================================

def clean(value: Any) -> Optional[str]:
    """
    Convert a value to a cleaned string.
    Return None for empty values.
    """

    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def normalize_brand(value: Any) -> Optional[str]:
    """
    Normalize manufacturer names so RC values can match
    market-reference brand names.
    """

    text = clean(value)

    if not text:
        return None

    text = text.lower()

    aliases = {

        "bmw india pvt ltd":
            "bmw",

        "bmw india private limited":
            "bmw",

        "mercedes benz":
            "mercedes-benz",

        "mercedes_benz":
            "mercedes-benz",

        "hyundai motor india ltd":
            "hyundai",

        "hyundai motor india":
            "hyundai",

        "tata motors":
            "tata",

        "tata motors ltd":
            "tata",

        "maruti suzuki india ltd":
            "maruti suzuki",

        "mg motor":
            "mg",
    }

    return aliases.get(
        text,
        text,
    )


def normalize_model(value: Any) -> Optional[str]:
    """
    Normalize a model name for comparison.

    Example:
        BMW X1 SDRIVE20D -> x1
        BMW X1 sDrive20d -> x1
    """

    text = clean(value)

    if not text:
        return None

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    text = text.replace(
        "-",
        " ",
    )

    # Remove manufacturer prefix.
    text = re.sub(
        r"^bmw\s+",
        "",
        text,
    ).strip()

    model_families = [

        ("6 series gt", "6 series gt"),

        ("2 series gran coupe", "2 series"),

        ("2 series", "2 series"),

        ("3 series", "3 series"),

        ("5 series", "5 series"),

        ("7 series", "7 series"),

        ("x1", "x1"),

        ("x 1", "x1"),

        ("x3", "x3"),

        ("x 3", "x3"),

        ("x4", "x4"),

        ("x 4", "x4"),

        ("x5", "x5"),

        ("x 5", "x5"),

        ("x6", "x6"),

        ("x 6", "x6"),

        ("x7", "x7"),

        ("x 7", "x7"),

        ("z4", "z4"),

        ("m340i", "m340i"),

        ("m4", "m4"),
    ]

    for pattern, normalized in model_families:

        if pattern in text:
            return normalized

    return text


def normalize_variant(value: Any) -> Optional[str]:
    """
    Normalize variant names for approximate matching.
    """

    text = clean(value)

    if not text:
        return None

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def normalize_fuel(value: Any) -> Optional[str]:

    text = clean(value)

    if not text:
        return None

    value = text.lower()

    if "diesel" in value:
        return "Diesel"

    if "petrol" in value:
        return "Petrol"

    if "gasoline" in value:
        return "Petrol"

    if "cng" in value:
        return "CNG"

    if "lpg" in value:
        return "LPG"

    if "electric" in value:
        return "Electric"

    if value == "ev":
        return "Electric"

    if "hybrid" in value:
        return "Hybrid"

    return text.title()


def normalize_city(value: Any) -> Optional[str]:

    text = clean(value)

    if not text:
        return None

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip().lower()


def parse_year(value: Any) -> Optional[int]:
    """
    Extract a four-digit year from a value such as:
        2019
        07/2019
        2019-07-01
    """

    text = clean(value)

    if not text:
        return None

    match = re.search(
        r"(19|20)\d{2}",
        text,
    )

    if not match:
        return None

    return int(
        match.group(0)
    )


def parse_owner_number(value: Any) -> Optional[int]:

    text = clean(value)

    if not text:
        return None

    match = re.search(
        r"\d+",
        text,
    )

    if not match:
        return None

    return int(
        match.group(0)
    )


def clamp(
    value: float,
    low: float,
    high: float,
) -> float:

    return max(
        low,
        min(
            high,
            value,
        ),
    )


# ============================================================
# MARKET DATA
# ============================================================

def get_market_csv() -> Path:

    for path in CSV_CANDIDATES:

        if path.exists():
            return path

    raise FileNotFoundError(
        "Market reference CSV not found.\n\n"
        "Expected one of:\n"
        + "\n".join(
            str(path)
            for path in CSV_CANDIDATES
        )
    )


def load_market_data() -> list[dict[str, str]]:

    csv_path = get_market_csv()

    with csv_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:

        return list(
            csv.DictReader(
                file
            )
        )


# ============================================================
# COMPARABLE SCORING
# ============================================================

def comparable_score(
    vehicle: dict[str, Any],
    row: dict[str, str],
) -> float:
    """
    Score the similarity between the target vehicle and
    one market-reference record.

    Maximum:

        Brand    = 20
        Model    = 40
        Year     = 20
        Fuel     = 10
        City     = 10
        Variant  = 5
    """

    target_brand = normalize_brand(
        vehicle.get(
            "manufacturer"
        )
    )

    target_model = normalize_model(
        vehicle.get(
            "model"
        )
    )

    target_year = parse_year(
        vehicle.get(
            "manufacturing_date"
        )
    )

    target_fuel = normalize_fuel(
        vehicle.get(
            "fuel_type"
        )
    )

    target_city = normalize_city(
        vehicle.get(
            "city"
        )
    )

    target_variant = normalize_variant(
        vehicle.get(
            "variant"
        )
    )

    row_brand = normalize_brand(
        row.get(
            "brand"
        )
    )

    row_model = normalize_model(
        row.get(
            "model"
        )
    )

    row_year = parse_year(
        row.get(
            "year"
        )
    )

    row_fuel = normalize_fuel(
        row.get(
            "fuel"
        )
    )

    row_city = normalize_city(
        row.get(
            "city"
        )
    )

    row_variant = normalize_variant(
        row.get(
            "variant"
        )
    )

    score = 0.0

    # --------------------------------------------------------
    # Brand
    # --------------------------------------------------------

    if (
        target_brand
        and
        target_brand == row_brand
    ):
        score += 20

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    if (
        target_model
        and
        target_model == row_model
    ):
        score += 40

    # --------------------------------------------------------
    # Fuel
    # --------------------------------------------------------

    if (
        target_fuel
        and
        target_fuel == row_fuel
    ):
        score += 10

    # --------------------------------------------------------
    # City
    # --------------------------------------------------------

    if (
        target_city
        and
        target_city == row_city
    ):
        score += 10

    # --------------------------------------------------------
    # Year
    # --------------------------------------------------------

    if (
        target_year is not None
        and
        row_year is not None
    ):

        difference = abs(
            target_year - row_year
        )

        if difference == 0:
            score += 20

        elif difference == 1:
            score += 15

        elif difference == 2:
            score += 10

        elif difference == 3:
            score += 5

    # --------------------------------------------------------
    # Variant
    # --------------------------------------------------------

    if (
        target_variant
        and
        row_variant
    ):

        if target_variant == row_variant:

            score += 5

        elif (
            target_variant in row_variant
            or
            row_variant in target_variant
        ):

            score += 3

    return score


def find_comparables(
    vehicle: dict[str, Any],
) -> list[dict[str, Any]]:

    rows = load_market_data()

    ranked = []

    for row in rows:

        score = comparable_score(
            vehicle,
            row,
        )

        # Require at least brand + model-level relevance.
        if score < 60:
            continue

        item = dict(
            row
        )

        item["_score"] = score

        ranked.append(
            item
        )

    target_year = parse_year(
        vehicle.get(
            "manufacturing_date"
        )
    )

    def sort_key(row):

        row_year = parse_year(
            row.get(
                "year"
            )
        )

        year_difference = (
            abs(
                target_year - row_year
            )
            if (
                target_year is not None
                and
                row_year is not None
            )
            else 999
        )

        return (
            float(
                row.get(
                    "_score",
                    0,
                )
            ),
            -year_difference,
        )

    ranked.sort(
        key=sort_key,
        reverse=True,
    )

    return ranked[:10]


# ============================================================
# WEIGHTED REFERENCE VALUE
# ============================================================

def weighted_reference_value(
    rows: list[dict[str, Any]]
) -> Optional[int]:

    if not rows:
        return None

    weighted_total = 0.0
    total_weight = 0.0

    for row in rows:

        try:

            price = float(
                row[
                    "median_price_inr"
                ]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            continue

        score = float(
            row.get(
                "_score",
                60,
            )
        )

        # More relevant comparables receive more weight.
        weight = max(
            1.0,
            score / 20.0,
        )

        weighted_total += (
            price * weight
        )

        total_weight += weight

    if total_weight == 0:
        return None

    return int(
        round(
            weighted_total
            / total_weight
        )
    )


def reference_range(
    rows: list[dict[str, Any]]
) -> dict[str, Optional[int]]:

    lows = []
    highs = []

    for row in rows:

        try:

            lows.append(
                float(
                    row[
                        "min_price_inr"
                    ]
                )
            )

            highs.append(
                float(
                    row[
                        "max_price_inr"
                    ]
                )
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            continue

    if not lows:

        return {
            "low": None,
            "high": None,
        }

    return {
        "low": int(
            round(
                median(lows)
            )
        ),

        "high": int(
            round(
                median(highs)
            )
        ),
    }


# ============================================================
# VALUATION ADJUSTMENTS
# ============================================================

def mileage_adjustment(
    mileage_km: Any,
) -> float:
    """
    Prototype mileage adjustment.

    60,000 km = neutral
    Lower mileage = positive adjustment
    Higher mileage = negative adjustment
    """

    if mileage_km is None:
        return 0.0

    try:

        km = float(
            mileage_km
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0.0

    if km == 60000:
        return 0.0

    if km < 60000:

        return min(
            0.05,
            (60000 - km) / 600000,
        )

    return -min(
        0.15,
        (km - 60000) / 400000,
    )


def ownership_adjustment(
    owner_serial: Any,
) -> float:

    owner = parse_owner_number(
        owner_serial
    )

    if owner is None:
        return 0.0

    if owner <= 1:
        return 0.0

    if owner == 2:
        return -0.03

    return -0.06


def damage_adjustment(
    predicted_class: Any,
) -> float:

    value = clean(
        predicted_class
    )

    if not value:
        return 0.0

    value = value.lower()

    if "crushed" in value:

        return DAMAGE_ADJUSTMENTS[
            "crushed"
        ]

    if "breakage" in value:

        return DAMAGE_ADJUSTMENTS[
            "breakage"
        ]

    if "normal" in value:

        return DAMAGE_ADJUSTMENTS[
            "normal"
        ]

    return 0.0


def adjustment_amount(
    reference_value: int,
    percentage: float,
) -> int:

    return int(
        round(
            reference_value
            * percentage
        )
    )


# ============================================================
# CONFIDENCE
# ============================================================

def valuation_confidence(
    rows: list[dict[str, Any]],
    vehicle: dict[str, Any],
) -> int:

    if not rows:
        return 0

    best_score = float(
        rows[0].get(
            "_score",
            0,
        )
    )

    if best_score >= 100:

        score = 88

    elif best_score >= 90:

        score = 82

    elif best_score >= 80:

        score = 76

    elif best_score >= 70:

        score = 68

    else:

        score = 58

    if len(rows) >= 3:
        score += 4

    if vehicle.get(
        "mileage_km"
    ) is not None:
        score += 3

    if vehicle.get(
        "city"
    ):
        score += 2

    return int(
        clamp(
            score,
            0,
            95,
        )
    )


# ============================================================
# MAIN VALUATION FUNCTION
# ============================================================

def evaluate_vehicle(
    vehicle: dict[str, Any],
    damage: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:

    vehicle = vehicle or {}

    damage = damage or {}

    # --------------------------------------------------------
    # Find market comparables
    # --------------------------------------------------------

    comparables = find_comparables(
        vehicle
    )

    if not comparables:

        return {
            "success": False,

            "message": (
                "No sufficiently close market-reference "
                "records were found for the supplied vehicle."
            ),

            "comparables_used": 0,
        }

    # --------------------------------------------------------
    # Calculate weighted reference
    # --------------------------------------------------------

    reference_value = weighted_reference_value(
        comparables
    )

    if reference_value is None:

        return {
            "success": False,

            "message": (
                "Comparable records were found, but valid "
                "median prices were not available."
            ),

            "comparables_used":
                len(comparables),
        }

    market_range = reference_range(
        comparables
    )

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------
    #
    # NO blanket age depreciation.
    #
    # The CSV already contains used-car prices for specific
    # vehicle years. Applying another 5% per year would
    # double-count depreciation.
    #
    # --------------------------------------------------------

    mileage_pct = mileage_adjustment(
        vehicle.get(
            "mileage_km"
        )
    )

    ownership_pct = ownership_adjustment(
        vehicle.get(
            "owner_serial"
        )
    )

    damage_pct = damage_adjustment(
        damage.get(
            "predicted_class"
        )
    )

    mileage_amount = adjustment_amount(
        reference_value,
        mileage_pct,
    )

    ownership_amount = adjustment_amount(
        reference_value,
        ownership_pct,
    )

    damage_amount = adjustment_amount(
        reference_value,
        damage_pct,
    )

    estimated_value = (
        reference_value
        +
        mileage_amount
        +
        ownership_amount
        +
        damage_amount
    )

    estimated_value = max(
        0,
        int(
            round(
                estimated_value
            )
        ),
    )

    confidence = valuation_confidence(
        rows=comparables,
        vehicle=vehicle,
    )

    # --------------------------------------------------------
    # Comparable output
    # --------------------------------------------------------

    comparable_output = []

    for row in comparables:

        try:

            median_price_value = int(
                float(
                    row[
                        "median_price_inr"
                    ]
                )
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            continue

        comparable_output.append(
            {
                "brand":
                    row.get(
                        "brand"
                    ),

                "model":
                    row.get(
                        "model"
                    ),

                "variant":
                    row.get(
                        "variant"
                    ),

                "year":
                    row.get(
                        "year"
                    ),

                "fuel":
                    row.get(
                        "fuel"
                    ),

                "city":
                    row.get(
                        "city"
                    ),

                "median_price_inr":
                    median_price_value,

                "matching_score":
                    round(
                        float(
                            row.get(
                                "_score",
                                0,
                            )
                        ),
                        1,
                    ),

                "source":
                    row.get(
                        "source"
                    ),

                "source_date":
                    row.get(
                        "source_date"
                    ),
            }
        )

    # --------------------------------------------------------
    # Return clean business response
    # --------------------------------------------------------

    return {

        "success": True,

        "valuation_method": (
            "Weighted comparable market references with "
            "mileage, ownership and damage adjustments. "
            "No blanket age depreciation is applied because "
            "the reference records already represent used-vehicle prices."
        ),

        "reference_dataset":
            get_market_csv().name,

        "reference_market_value_inr":
            reference_value,

        "adjustments": {

            "mileage": {

                "percentage":
                    round(
                        mileage_pct * 100,
                        2,
                    ),

                "amount_inr":
                    mileage_amount,
            },

            "ownership": {

                "percentage":
                    round(
                        ownership_pct * 100,
                        2,
                    ),

                "amount_inr":
                    ownership_amount,
            },

            "damage": {

                "percentage":
                    round(
                        damage_pct * 100,
                        2,
                    ),

                "amount_inr":
                    damage_amount,

                "input":
                    damage.get(
                        "predicted_class"
                    ),
            },
        },

        "estimated_fair_value_inr":
            estimated_value,

        "valuation_range_inr":
            market_range,

        "valuation_confidence_percent":
            confidence,

        "comparables_used":
            len(
                comparable_output
            ),

        "comparables":
            comparable_output,
    }