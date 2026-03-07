"""Probate chat flow engine — 13 steps with branching logic."""

from typing import Any

PROBATE_QUESTIONS: list[dict] = [
    {
        "id": "service_type",
        "step": 1,
        "text": "What type of probate service do you need?",
        "type": "single_choice",
        "options": [
            {
                "value": "grant_only",
                "label": "Grant of Probate only",
                "description": "You'll handle the estate administration yourself",
            },
            {
                "value": "full_administration",
                "label": "Full estate administration",
                "description": "Solicitor handles everything from start to finish",
            },
        ],
    },
    {
        "id": "estate_value",
        "step": 2,
        "text": "What is the approximate gross value of the estate (before debts)?",
        "type": "single_choice",
        "options": [
            {"value": "under_100k", "label": "Under £100,000", "range": [0, 100000]},
            {"value": "100k_325k", "label": "£100,000 – £325,000", "range": [100000, 325000]},
            {"value": "325k_650k", "label": "£325,000 – £650,000", "range": [325000, 650000]},
            {"value": "650k_1m", "label": "£650,000 – £1,000,000", "range": [650000, 1000000]},
            {"value": "over_1m", "label": "Over £1,000,000", "range": [1000000, None]},
        ],
    },
    {
        "id": "has_will",
        "step": 3,
        "text": "Did the deceased leave a valid Will?",
        "type": "single_choice",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No (intestacy)"},
            {"value": "unknown", "label": "I'm not sure"},
        ],
    },
    {
        "id": "iht400",
        "step": 4,
        "text": "Is the estate likely to require an IHT400 form (taxable estate / inheritance tax applies)?",
        "type": "single_choice",
        "options": [
            {"value": "yes", "label": "Yes — the estate may be taxable"},
            {"value": "no", "label": "No — the estate is below the nil-rate band"},
            {"value": "unknown", "label": "I'm not sure"},
        ],
        "hint": "The inheritance tax threshold is currently £325,000 (or up to £500,000 with the residence nil-rate band).",
    },
    {
        "id": "uk_domiciled",
        "step": 5,
        "text": "Was the deceased domiciled (permanently resident) in England or Wales?",
        "type": "single_choice",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
            {"value": "unknown", "label": "I'm not sure"},
        ],
    },
    {
        "id": "uk_property_count",
        "step": 6,
        "text": "How many UK properties did the deceased own?",
        "type": "single_choice",
        "options": [
            {"value": "0", "label": "None"},
            {"value": "1", "label": "1"},
            {"value": "2", "label": "2"},
            {"value": "3plus", "label": "3 or more"},
        ],
    },
    {
        "id": "bank_account_count",
        "step": 7,
        "text": "How many bank or building society accounts did the deceased have?",
        "type": "single_choice",
        "options": [
            {"value": "0", "label": "None"},
            {"value": "1_3", "label": "1 – 3"},
            {"value": "4_6", "label": "4 – 6"},
            {"value": "7plus", "label": "7 or more"},
        ],
    },
    {
        "id": "investments_count",
        "step": 8,
        "text": "Did the estate include stocks, shares, ISAs or other investments?",
        "type": "single_choice",
        "options": [
            {"value": "none", "label": "None"},
            {"value": "simple", "label": "Yes — straightforward (e.g. ISA, NS&I)"},
            {"value": "complex", "label": "Yes — complex (e.g. portfolio, business shares)"},
        ],
    },
    {
        "id": "overseas_assets",
        "step": 9,
        "text": "Were there any overseas assets or foreign bank accounts?",
        "type": "single_choice",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
        ],
    },
    {
        "id": "beneficiary_count",
        "step": 10,
        "text": "How many beneficiaries will inherit from the estate?",
        "type": "single_choice",
        "options": [
            {"value": "1_2", "label": "1 – 2"},
            {"value": "3_5", "label": "3 – 5"},
            {"value": "6plus", "label": "6 or more"},
        ],
    },
    {
        "id": "location",
        "step": 11,
        "text": "What is your postcode? We'll use this to find solicitors near you.",
        "type": "postcode",
        "placeholder": "e.g. SW1A 1AA",
    },
    {
        "id": "location_preference",
        "step": 12,
        "text": "Do you prefer a local solicitor or are you happy to work remotely?",
        "type": "single_choice",
        "options": [
            {"value": "local", "label": "I prefer a local solicitor"},
            {"value": "remote", "label": "I'm happy to work remotely"},
            {"value": "no_preference", "label": "No preference"},
        ],
    },
    {
        "id": "ranking_preference",
        "step": 13,
        "text": "What matters most to you when choosing a solicitor?",
        "type": "single_choice",
        "options": [
            {
                "value": "price",
                "label": "Best price",
                "description": "Show me the most affordable options",
            },
            {
                "value": "reputation",
                "label": "Best reviews",
                "description": "Show me the highest-rated firms",
            },
            {
                "value": "distance",
                "label": "Closest to me",
                "description": "Show me firms nearest to my location",
            },
            {
                "value": "balanced",
                "label": "Balanced recommendation",
                "description": "A mix of price, reputation and location",
            },
        ],
    },
]

# Map question id → index for quick lookup
QUESTION_INDEX: dict[str, int] = {q["id"]: i for i, q in enumerate(PROBATE_QUESTIONS)}


def get_first_question() -> dict:
    return PROBATE_QUESTIONS[0]


def get_next_question(current_question_id: str, answers: dict) -> dict | None:
    """Return the next question given current answers, or None if flow is complete."""
    current_idx = QUESTION_INDEX.get(current_question_id)
    if current_idx is None:
        return None

    next_idx = current_idx + 1
    if next_idx >= len(PROBATE_QUESTIONS):
        return None

    return PROBATE_QUESTIONS[next_idx]


def is_flow_complete(answers: dict) -> bool:
    """Return True when all required questions have been answered."""
    last_question = PROBATE_QUESTIONS[-1]
    return last_question["id"] in answers


def get_estate_value_midpoint(band: str) -> float:
    """Convert estate value band to midpoint for price calculation."""
    band_map = {
        "under_100k": 75000,
        "100k_325k": 212500,
        "325k_650k": 487500,
        "650k_1m": 825000,
        "over_1m": 1500000,
    }
    return band_map.get(band, 212500)


def get_complexity_flags(answers: dict) -> dict[str, Any]:
    """Extract flags that affect pricing from answers."""
    return {
        "service_type": answers.get("service_type", "full_administration"),
        "estate_value_band": answers.get("estate_value", "100k_325k"),
        "estate_value": get_estate_value_midpoint(answers.get("estate_value", "100k_325k")),
        "has_iht400": answers.get("iht400") == "yes",
        "has_overseas_assets": answers.get("overseas_assets") == "yes",
        "has_complex_investments": answers.get("investments_count") == "complex",
        "property_count": answers.get("uk_property_count", "0"),
        "postcode": answers.get("location", ""),
        "ranking_preference": answers.get("ranking_preference", "balanced"),
        "location_preference": answers.get("location_preference", "no_preference"),
    }
