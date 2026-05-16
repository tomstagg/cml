"""Conveyancing intake — pathway-aware question schema per the 14.05.26 spec.

The intake is fully deterministic for MVP:
- Q1 picks the pathway (Buying / Selling / Both).
- Each pathway has a different set of follow-up questions.
- Q4 / Q3S&P shows pathway-specific modifier options.
- Q5 is an optional postcode for distance ranking.

Variable names match the spec verbatim (purchase_property_value etc.) so the
pricing engine and ranking code read against the spec without translation.
"""

import re
from typing import Any

# ── Pathway types ────────────────────────────────────────────────────────────
# Q1's three accepted answers, used downstream to gate visible questions and
# to drive pricing-engine routing.
PATHWAY_PURCHASE = "purchase"
PATHWAY_SALE = "sale"
PATHWAY_COMBINED = "combined"

# Mapping of the user-facing Q1 option values to the internal pathway tokens.
TRANSACTION_TYPE_TO_PATHWAY = {
    "buying": PATHWAY_PURCHASE,
    "selling": PATHWAY_SALE,
    "selling_and_buying": PATHWAY_COMBINED,
}


# ── Question schema ──────────────────────────────────────────────────────────
# Every question is tagged with the pathways it belongs to. The active pathway
# (derived from the user's Q1 answer) decides whether a given question is shown.
QUESTIONS: list[dict] = [
    {
        "id": "transaction_type",
        "step": 1,
        "pathways": [PATHWAY_PURCHASE, PATHWAY_SALE, PATHWAY_COMBINED],
        "section": "Your move",
        "text": (
            "Thank you for using Choose My Lawyer. To start with, please can you "
            "tell me if you are buying a property, selling a property, or are you "
            "buying & selling?"
        ),
        "type": "single_choice",
        "options": [
            {"value": "buying", "label": "Buying"},
            {"value": "selling", "label": "Selling"},
            {"value": "selling_and_buying", "label": "Selling & buying"},
        ],
    },
    # ── Buying-only pathway ──────────────────────────────────────────────────
    {
        "id": "purchase_tenure_type",
        "step": 2,
        "pathways": [PATHWAY_PURCHASE],
        "section": "About the property",
        "text": "Thank you. Is the property you are buying freehold or leasehold?",
        "type": "tenure_with_unsure",
        "options": [
            {"value": "freehold", "label": "Freehold"},
            {"value": "leasehold", "label": "Leasehold"},
            {"value": "unsure", "label": "I'm not sure"},
        ],
    },
    {
        "id": "purchase_property_value",
        "step": 3,
        "pathways": [PATHWAY_PURCHASE],
        "section": "About the property",
        "text": "Please enter the purchase price of the property.",
        "type": "currency",
        "placeholder": "£275,000",
    },
    # ── Selling-only pathway ─────────────────────────────────────────────────
    {
        "id": "sale_tenure_type",
        "step": 2,
        "pathways": [PATHWAY_SALE],
        "section": "About the property",
        "text": "Thank you. Is the property you are selling freehold or leasehold?",
        "type": "tenure_with_unsure",
        "options": [
            {"value": "freehold", "label": "Freehold"},
            {"value": "leasehold", "label": "Leasehold"},
            {"value": "unsure", "label": "I'm not sure"},
        ],
    },
    {
        "id": "sale_property_value",
        "step": 3,
        "pathways": [PATHWAY_SALE],
        "section": "About the property",
        "text": "Please enter the sale price of the property.",
        "type": "currency",
        "placeholder": "£275,000",
    },
    # ── Combined pathway ─────────────────────────────────────────────────────
    # One unified question block captures tenure + price for both the property
    # being bought and the property being sold. Stored answer is a dict
    # {"purchase_tenure_type": ..., "purchase_property_value": ...,
    #  "sale_tenure_type": ..., "sale_property_value": ...} — these keys are
    # later flattened into the same flag space as the single-pathway flows.
    {
        "id": "combined_property_details",
        "step": 2,
        "pathways": [PATHWAY_COMBINED],
        "section": "About the move",
        "text": "Thank you. Please enter a few details about the properties involved in your move.",
        "type": "dual_property_block",
        "tenure_options": [
            {"value": "freehold", "label": "Freehold"},
            {"value": "leasehold", "label": "Leasehold"},
            {"value": "unsure", "label": "I'm not sure"},
        ],
    },
    # ── Shared: transaction details (Q4 / Q3S&P) ─────────────────────────────
    # Checkbox group, options gated by pathway in `dynamic_options()`.
    {
        "id": "transaction_details",
        "step": 4,
        "pathways": [PATHWAY_PURCHASE, PATHWAY_SALE],
        "section": "Transaction details",
        "text": "A few quick details about the transaction. Please select any that apply.",
        "type": "checkbox_group",
        "hint": "You can continue without selecting any options.",
    },
    {
        "id": "transaction_details",
        "step": 3,
        "pathways": [PATHWAY_COMBINED],
        "section": "Transaction details",
        "text": "A few quick details about the transaction. Please select any that apply.",
        "type": "checkbox_group",
        "hint": "You can continue without selecting any options.",
    },
    # ── Shared: distance preference (Q5) ─────────────────────────────────────
    {
        "id": "distance_preference",
        "step": 5,
        "pathways": [PATHWAY_PURCHASE, PATHWAY_SALE],
        "section": "Your area",
        "text": (
            "Would you like distance to each firm's nearest office included in your "
            "results? This may help if you want to see your lawyer in person. If so, "
            "please enter your postcode below. Otherwise, you can continue straight "
            "to your results."
        ),
        "type": "optional_postcode",
        "placeholder": "e.g. B1 1AA",
    },
    {
        "id": "distance_preference",
        "step": 4,
        "pathways": [PATHWAY_COMBINED],
        "section": "Your area",
        "text": (
            "Would you like distance to each firm's nearest office included in your "
            "results? This may help if you want to see your lawyer in person. If so, "
            "please enter your postcode below. Otherwise, you can continue straight "
            "to your results."
        ),
        "type": "optional_postcode",
        "placeholder": "e.g. B1 1AA",
    },
]


# All checkbox-group flag IDs the intake can produce. The same set is sent to
# the frontend (via `dynamic_options`) and consumed by `get_intake_flags`.
MODIFIER_OPTIONS_BUYING: list[dict] = [
    {
        "value": "mortgage_required",
        "label": "I'm buying with a mortgage",
    },
    {
        "value": "new_build",
        "label": "The property is a new build",
        "pathways": [PATHWAY_PURCHASE, PATHWAY_COMBINED],
        "tenures": ["freehold"],
    },
    {
        "value": "new_lease",
        "label": "This is a new lease",
        "pathways": [PATHWAY_PURCHASE, PATHWAY_COMBINED],
        "tenures": ["leasehold"],
    },
    {
        "value": "shared_ownership_or_help_to_buy",
        "label": "I'm using shared ownership or Help to Buy",
    },
    {
        "value": "gifted_deposit",
        "label": "Part of the deposit is being gifted",
    },
    {
        "value": "unregistered_title_purchase",
        "label": "The property I am buying is unregistered",
    },
]

MODIFIER_OPTIONS_SELLING: list[dict] = [
    {
        "value": "additional_mortgage_redemption",
        "label": "There is more than one mortgage or secured loan against the property I'm selling",
    },
    {
        "value": "unregistered_title_sale",
        "label": "The property I'm selling is unregistered",
    },
]


# ── Validation regex ─────────────────────────────────────────────────────────
POSTCODE_REGEX = re.compile(r"^[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}$", re.IGNORECASE)


def get_pathway(answers: dict) -> str | None:
    """Resolve the active pathway from Q1's answer, or None if unanswered."""
    raw = answers.get("transaction_type")
    if not isinstance(raw, str):
        return None
    return TRANSACTION_TYPE_TO_PATHWAY.get(raw)


def visible_questions(pathway: str | None) -> list[dict]:
    """Return the ordered question list for the given pathway."""
    if pathway is None:
        # Pre-Q1: only Q1 is visible.
        return [q for q in QUESTIONS if q["id"] == "transaction_type"]
    return [q for q in QUESTIONS if pathway in q["pathways"]]


def dynamic_options(question_id: str, answers: dict) -> list[dict]:
    """Resolve the visible modifier options for the transaction_details step
    based on the active pathway and tenures recorded so far.
    """
    if question_id != "transaction_details":
        return []
    pathway = get_pathway(answers)
    if pathway is None:
        return []

    purchase_tenure = _resolve_tenure(answers, "purchase")
    sale_tenure = _resolve_tenure(answers, "sale")

    out: list[dict] = []
    if pathway in (PATHWAY_PURCHASE, PATHWAY_COMBINED):
        for opt in MODIFIER_OPTIONS_BUYING:
            allowed_pathways = opt.get("pathways") or [PATHWAY_PURCHASE, PATHWAY_COMBINED]
            if pathway not in allowed_pathways:
                continue
            allowed_tenures = opt.get("tenures")
            if allowed_tenures and (purchase_tenure not in allowed_tenures):
                continue
            out.append({"value": opt["value"], "label": opt["label"]})
    if pathway in (PATHWAY_SALE, PATHWAY_COMBINED):
        for opt in MODIFIER_OPTIONS_SELLING:
            allowed_tenures = opt.get("tenures")
            if allowed_tenures and (sale_tenure not in allowed_tenures):
                continue
            out.append({"value": opt["value"], "label": opt["label"]})
    return out


def _resolve_tenure(answers: dict, side: str) -> str | None:
    """Look up the tenure for the given side ('purchase' or 'sale')."""
    direct_key = f"{side}_tenure_type"
    if direct_key in answers:
        return answers[direct_key]
    combined = answers.get("combined_property_details")
    if isinstance(combined, dict):
        return combined.get(direct_key)
    return None


def first_question(answers: dict | None = None) -> dict:
    """Return the question the user should see first (always Q1 today)."""
    answers = answers or {}
    pathway = get_pathway(answers)
    return visible_questions(pathway)[0]


def next_question(answers: dict) -> dict | None:
    """Return the next unanswered question in the current pathway, or None
    if the flow is complete.

    Treats "I'm not sure" tenure answers as non-progressing — the same
    question is re-shown until a definitive freehold/leasehold value is given.
    """
    pathway = get_pathway(answers)
    if pathway is None:
        # No transaction_type yet → show Q1.
        return next((q for q in QUESTIONS if q["id"] == "transaction_type"), None)

    for q in visible_questions(pathway):
        qid = q["id"]
        if not _is_answered(qid, answers, pathway):
            return q
    return None


def _is_answered(question_id: str, answers: dict, pathway: str) -> bool:
    """Has the user supplied a usable (non-pause) answer for this question?"""
    if question_id == "transaction_details":
        # Optional — counts as answered once present in the dict, even if the
        # user selected nothing.
        return question_id in answers
    if question_id == "distance_preference":
        return question_id in answers
    if question_id == "combined_property_details":
        block = answers.get(question_id)
        if not isinstance(block, dict):
            return False
        tenures_ok = block.get("purchase_tenure_type") in ("freehold", "leasehold") and block.get(
            "sale_tenure_type"
        ) in ("freehold", "leasehold")
        prices_ok = _is_positive_number(block.get("purchase_property_value")) and (
            _is_positive_number(block.get("sale_property_value"))
        )
        return tenures_ok and prices_ok
    if question_id in ("purchase_tenure_type", "sale_tenure_type"):
        return answers.get(question_id) in ("freehold", "leasehold")
    if question_id in ("purchase_property_value", "sale_property_value"):
        return _is_positive_number(answers.get(question_id))
    return question_id in answers


def _is_positive_number(value: Any) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def is_flow_complete(answers: dict) -> bool:
    return next_question(answers) is None


def find_question(question_id: str, pathway: str | None) -> dict | None:
    """Look up a question definition for editing / revise mode."""
    if pathway is None:
        candidates = [q for q in QUESTIONS if q["id"] == question_id]
    else:
        candidates = [q for q in QUESTIONS if q["id"] == question_id and pathway in q["pathways"]]
    return candidates[0] if candidates else None


# ── Answer validation ────────────────────────────────────────────────────────
def validate_answer(question_id: str, answer: Any, answers: dict) -> tuple[bool, str | None]:
    """Validate a submitted answer against its question definition.

    Combined-pathway dual_property_block expects a dict payload; checkbox_group
    accepts a list (possibly empty); single_choice and currency follow their
    usual rules.
    """
    pathway = get_pathway(answers)
    question = find_question(question_id, pathway)
    if question is None:
        return False, f"Unknown question: {question_id}"

    qtype = question["type"]

    if qtype == "single_choice" or qtype == "tenure_with_unsure":
        if not isinstance(answer, str):
            return False, "Please pick one of the options."
        valid = {opt["value"] for opt in question.get("options", [])}
        if answer not in valid:
            return False, f"'{answer}' is not a valid option for {question_id}."
        return True, None

    if qtype == "currency":
        return (
            (True, None)
            if _is_positive_number(answer)
            else (
                False,
                "Please enter a numeric amount greater than zero.",
            )
        )

    if qtype == "dual_property_block":
        if not isinstance(answer, dict):
            return False, "Combined property details must be a dict."
        required_tenure_keys = ("purchase_tenure_type", "sale_tenure_type")
        for key in required_tenure_keys:
            if answer.get(key) not in ("freehold", "leasehold", "unsure"):
                return False, f"Please pick a tenure for {key}."
        for key in ("purchase_property_value", "sale_property_value"):
            if not _is_positive_number(answer.get(key)):
                return False, f"Please enter a numeric amount for {key}."
        return True, None

    if qtype == "checkbox_group":
        if answer is None:
            return True, None  # Optional — empty selection allowed.
        if not isinstance(answer, list):
            return False, "Transaction details must be a list of selected flags."
        valid = {opt["value"] for opt in dynamic_options(question_id, answers)}
        for selected in answer:
            if selected not in valid:
                return False, f"'{selected}' is not available for this transaction."
        return True, None

    if qtype == "optional_postcode":
        if answer in (None, ""):
            return True, None
        if not isinstance(answer, str) or not POSTCODE_REGEX.match(answer.strip()):
            return False, "Please enter a valid UK postcode (or leave blank)."
        return True, None

    return False, f"Unsupported question type: {qtype}"


# ── Intake → pricing/ranking flags ───────────────────────────────────────────
_TRUTHY = {"true", "yes", "1"}


def _flag(values: list[str] | None, name: str) -> bool:
    if not values:
        return False
    return name in values


def get_intake_flags(answers: dict) -> dict[str, Any]:
    """Project raw chat answers into the flat dict consumed by the price
    calculator and the search/ranking layer.
    """
    pathway = get_pathway(answers) or PATHWAY_PURCHASE

    # Combined-pathway answers are nested in a sub-dict; flatten here.
    combined = (
        answers.get("combined_property_details")
        if isinstance(answers.get("combined_property_details"), dict)
        else {}
    )

    def _coerce_price(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    purchase_tenure = (
        answers.get("purchase_tenure_type") or combined.get("purchase_tenure_type") or None
    )
    sale_tenure = answers.get("sale_tenure_type") or combined.get("sale_tenure_type") or None
    purchase_value = _coerce_price(
        answers.get("purchase_property_value") or combined.get("purchase_property_value")
    )
    sale_value = _coerce_price(
        answers.get("sale_property_value") or combined.get("sale_property_value")
    )

    modifiers = answers.get("transaction_details") or []
    if not isinstance(modifiers, list):
        modifiers = []

    user_postcode_raw = answers.get("distance_preference") or ""
    user_postcode = user_postcode_raw.strip() if isinstance(user_postcode_raw, str) else ""

    return {
        "pathway": pathway,
        "transaction_type": answers.get("transaction_type", ""),
        # Purchase side (None / 0 if pathway is sale-only)
        "purchase_tenure_type": purchase_tenure,
        "purchase_property_value": purchase_value,
        # Sale side
        "sale_tenure_type": sale_tenure,
        "sale_property_value": sale_value,
        # Modifier flags — boolean per individual trigger.
        "mortgage_required": _flag(modifiers, "mortgage_required"),
        "new_build": _flag(modifiers, "new_build"),
        "new_lease": _flag(modifiers, "new_lease"),
        "shared_ownership_or_help_to_buy": _flag(modifiers, "shared_ownership_or_help_to_buy"),
        "gifted_deposit": _flag(modifiers, "gifted_deposit"),
        "unregistered_title_purchase": _flag(modifiers, "unregistered_title_purchase"),
        "unregistered_title_sale": _flag(modifiers, "unregistered_title_sale"),
        "additional_mortgage_redemption": _flag(modifiers, "additional_mortgage_redemption"),
        # Distance
        "user_postcode": user_postcode,
        "distance_included": bool(user_postcode),
    }
