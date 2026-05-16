"""Conveyancing intake flow — 9 steps with validation per requirements §5.1.3.

Personal contact details (first/last name, email, phone) are gathered at the
Proceed / Callback conversion step, not during intake.
"""

import re
from typing import Any

# Conveyancing intake question schema. Step numbers are 1-based and define the
# canonical order the chat (and Figma stepper) walks the user through.
CONVEYANCING_QUESTIONS: list[dict] = [
    {
        "id": "purchase_price",
        "step": 1,
        "section": "About your case",
        "text": "What is the purchase price of the property?",
        "type": "currency",
        "placeholder": "£275,000",
        "hint": "Enter the agreed price (or your best estimate).",
    },
    {
        "id": "tenure",
        "step": 2,
        "section": "About your case",
        "text": "Is the property freehold or leasehold?",
        "type": "single_choice",
        "options": [
            {"value": "freehold", "label": "Freehold"},
            {"value": "leasehold", "label": "Leasehold"},
            {"value": "unknown", "label": "I'm not sure"},
        ],
    },
    {
        "id": "property_postcode",
        "step": 3,
        "section": "About your case",
        "text": "What is the property's postcode?",
        "type": "postcode",
        "placeholder": "e.g. B1 1AA",
        "hint": "We use this to confirm the property is within our pilot area.",
    },
    {
        "id": "mortgage",
        "step": 4,
        "section": "About your case",
        "text": "Will you need a mortgage to fund the purchase?",
        "type": "single_choice",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
        ],
    },
    {
        "id": "new_build",
        "step": 5,
        "section": "About your case",
        "text": "Is the property a new build?",
        "type": "single_choice",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
        ],
    },
    {
        "id": "help_to_buy_isa",
        "step": 6,
        "section": "About your case",
        "text": "Are you using a Help to Buy ISA?",
        "type": "single_choice",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
        ],
    },
    {
        "id": "shared_ownership",
        "step": 7,
        "section": "About your case",
        "text": "Is this a shared ownership purchase?",
        "type": "single_choice",
        "options": [
            {"value": "yes", "label": "Yes"},
            {"value": "no", "label": "No"},
        ],
    },
    {
        "id": "scorecard_preference",
        "step": 8,
        "section": "Ranking preference",
        "text": "How would you like firms to be ranked?",
        "type": "single_choice",
        "options": [
            {
                "value": "balanced",
                "label": "Balanced recommendation",
                "description": "A blend of reputation, price, complaints, regulatory record, distance and number of offices.",
            },
            {
                "value": "reputation",
                "label": "Reputation first",
                "description": "Prioritise firms with the best reviews.",
            },
            {
                "value": "price",
                "label": "Best price",
                "description": "Prioritise firms with the lowest total quoted cost.",
            },
            {
                "value": "complaints",
                "label": "Strong complaints record",
                "description": "Prioritise firms with the fewest Legal Ombudsman decisions.",
            },
            {
                "value": "regulatory",
                "label": "Strong regulatory record",
                "description": "Prioritise firms with the cleanest SRA / SDT history.",
            },
            {
                "value": "distance",
                "label": "Closest to me",
                "description": "Prioritise firms nearest to your postcode.",
            },
            {
                "value": "offices",
                "label": "Larger firms",
                "description": "Prioritise firms with more offices.",
            },
        ],
    },
    {
        "id": "include_distance",
        "step": 9,
        "section": "Ranking preference",
        "text": "Should distance to a firm's nearest office be factored into the ranking?",
        "type": "single_choice",
        "options": [
            {
                "value": "yes",
                "label": "Yes — include distance",
                "description": "We'll ask for your postcode next.",
            },
            {
                "value": "no",
                "label": "No — exclude distance",
                "description": "Other factors will be re-balanced to compensate.",
            },
        ],
    },
]

QUESTION_INDEX: dict[str, int] = {q["id"]: i for i, q in enumerate(CONVEYANCING_QUESTIONS)}

# UK postcode (matches frontend regex).
POSTCODE_REGEX = re.compile(r"^[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}$", re.IGNORECASE)
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Permissive UK phone — allow +, spaces, digits, and require at least 10 digits.
PHONE_REGEX = re.compile(r"^[+\d][\d\s]{8,}$")


def get_first_question() -> dict:
    return CONVEYANCING_QUESTIONS[0]


def get_question(question_id: str) -> dict | None:
    idx = QUESTION_INDEX.get(question_id)
    return CONVEYANCING_QUESTIONS[idx] if idx is not None else None


def get_next_question(current_question_id: str, answers: dict) -> dict | None:
    """Return the next question; skip step 9's follow-up postcode if user
    chose to exclude distance, or vice-versa.

    With the current 13-step schema there are no conditional skips — but this
    function is the natural place to add them later (e.g. distance follow-up).
    """
    current_idx = QUESTION_INDEX.get(current_question_id)
    if current_idx is None:
        return None

    next_idx = current_idx + 1
    if next_idx >= len(CONVEYANCING_QUESTIONS):
        return None

    return CONVEYANCING_QUESTIONS[next_idx]


def is_flow_complete(answers: dict) -> bool:
    """All required questions answered."""
    last_question = CONVEYANCING_QUESTIONS[-1]
    return last_question["id"] in answers


def validate_answer(question_id: str, answer: Any) -> tuple[bool, str | None]:
    """Return (ok, error_message) for the given answer.

    Backend mirrors the frontend's per-step validation so malformed payloads
    are rejected with a friendly 400 rather than silently stored.
    """
    question = get_question(question_id)
    if question is None:
        return False, f"Unknown question: {question_id}"

    qtype = question["type"]
    answer_str = answer if isinstance(answer, str) else str(answer)

    if qtype == "single_choice":
        valid_values = {opt["value"] for opt in question.get("options", [])}
        if answer_str not in valid_values:
            return False, f"'{answer_str}' is not a valid option for {question_id}"

    elif qtype == "currency":
        cleaned = answer_str.replace(",", "").replace("£", "").strip()
        try:
            value = float(cleaned)
        except ValueError:
            return False, "Please enter a numeric purchase price."
        if value <= 0:
            return False, "Purchase price must be greater than zero."

    elif qtype == "postcode":
        if not POSTCODE_REGEX.match(answer_str.strip()):
            return False, "Please enter a valid UK postcode."

    elif qtype == "text":
        if not answer_str.strip():
            return False, "This field is required."

    elif qtype == "email":
        if not EMAIL_REGEX.match(answer_str.strip()):
            return False, "Please enter a valid email address."

    elif qtype == "tel":
        cleaned = answer_str.replace(" ", "")
        if not PHONE_REGEX.match(cleaned):
            return False, "Please enter a valid phone number."

    return True, None


def get_intake_flags(answers: dict) -> dict[str, Any]:
    """Normalise raw chat answers into a flat dict consumed by the price
    calculator and the ranker.

    `purchase_price` is coerced to a float; yes/no answers to bool;
    `scorecard_preference` defaults to balanced; `include_distance` defaults
    to False.
    """

    def _yn(value: str | None) -> bool:
        return str(value).lower() in {"yes", "true", "1"}

    raw_price = str(answers.get("purchase_price", "0")).replace(",", "").replace("£", "").strip()
    try:
        purchase_price = float(raw_price)
    except ValueError:
        purchase_price = 0.0

    return {
        "purchase_price": purchase_price,
        "tenure": answers.get("tenure", "freehold"),
        "transaction_type": answers.get("transaction_type", "purchase"),
        "property_postcode": answers.get("property_postcode", ""),
        "mortgage": _yn(answers.get("mortgage")),
        "new_build": _yn(answers.get("new_build")),
        "help_to_buy_isa": _yn(answers.get("help_to_buy_isa")),
        "shared_ownership": _yn(answers.get("shared_ownership")),
        "scorecard_preference": answers.get("scorecard_preference", "balanced"),
        "include_distance": _yn(answers.get("include_distance")),
    }
