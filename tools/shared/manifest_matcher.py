"""
manifest_matcher.py — Matches document requests against manifest entries
and determines which specifications are satisfied.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Document-type alias maps
# ---------------------------------------------------------------------------

_DOCTYPE_ALIASES: dict[str, set[str]] = {
    "personal bank statements": {"bank statement", "bank statements"},
    "bank statement": {"personal bank statements", "bank statements"},
    "bank statements": {"personal bank statements", "bank statement"},
    "hazard insurance": {"homeowners insurance", "property insurance", "insurance binder"},
    "government-issued photo id": {"drivers license", "passport", "photo id", "identification"},
    "irs 4506-c authorization": {"4506-c", "4506c", "irs form 4506-c", "tax transcript authorization"},
    "purchase contract": {"sales contract", "purchase agreement", "contract of sale"},
    "rental agreement": {"lease agreement", "lease", "rental lease"},
    "appraisal report": {"appraisal report (urar)", "appraisal"},
    "credit report": {"tri-merge credit report", "credit report (rmcr)"},
    "verification of employment": {"voe", "verbal verification of employment"},
    "verification of mortgage": {"vom", "mortgage verification"},
    "verification of deposit": {"vod", "deposit verification"},
    "verification of rent": {"vor", "rent verification"},
    "rental income calculations worksheet": {"dscr calculation worksheet", "dscr documentation"},
    "flood hazard determination": {"flood certification", "flood determination"},
    "flood certification": {"flood hazard determination", "flood determination"},
    "owner occupancy certification": {"occupancy affidavit", "occupancy certification"},
    "title commitment": {"title report", "preliminary title report"},
    "borrowers authorization": {"borrower authorization", "borrower authorization form", "borrower certification as to business purpose"},
    "borrower certification as to business purpose": {"borrowers authorization", "borrower authorization"},
    "investment account statement": {"investment statement", "brokerage statement"},
    "urla 1003": {"loan application", "1003", "uniform residential loan application"},
}

# Blanket aliases: if matched, ALL specs are considered satisfied
_DOCTYPE_BLANKET_ALIASES: dict[str, set[str]] = {
    "borrower certification as to business purpose": {"borrowers authorization"},
}


def get_aliases(doc_type: str) -> set[str]:
    """Return all names that count as the same document."""
    key = doc_type.strip().lower()
    aliases = {key, key.replace(" ", "_"), key.replace("_", " ")}
    for alias_map in (_DOCTYPE_ALIASES, _DOCTYPE_BLANKET_ALIASES):
        for mapped in alias_map.get(key, set()):
            m = mapped.strip().lower()
            aliases.update({m, m.replace(" ", "_"), m.replace("_", " ")})
    return aliases


def is_blanket_alias(doc_type: str, matched_name: str) -> bool:
    """Return True if this match means ALL specs are satisfied."""
    key = doc_type.strip().lower()
    blanket_names = _DOCTYPE_BLANKET_ALIASES.get(key, set())
    return matched_name.strip().lower() in blanket_names


def find_matching_manifest_docs(
    doc_type: str,
    manifest_docs: list[dict],
) -> list[dict]:
    """Find all manifest documents matching the document_type (including aliases)."""
    all_names = get_aliases(doc_type)
    matches = []

    for mdoc in manifest_docs:
        doc_name = (mdoc.get("detected_document_type") or "").strip().lower()
        if doc_name and (doc_name in all_names or doc_name.replace(" ", "_") in all_names or doc_name.replace("_", " ") in all_names):
            matches.append(mdoc)

    return matches


# ---------------------------------------------------------------------------
# Spec satisfaction checking
# ---------------------------------------------------------------------------

# Maps keywords found in spec text → manifest extracted_field keys that prove satisfaction
SPEC_KEYWORD_TO_FIELDS: dict[str, list[str]] = {
    "purchase price": ["purchasePrice", "purchase_price", "salesPrice", "sales_price", "priceOfPriorSaleOrTransfer"],
    "fully executed": ["signed", "dateSigned", "date_signed"],
    "all signatures": ["signed", "dateSigned", "date_signed"],
    "signature": ["signed", "dateSigned", "date_signed"],
    "property address": ["propertyAddress", "property_address", "fullAddress", "address1", "statementAddress"],
    "subject property": ["propertyAddress", "property_address", "fullAddress", "address1"],
    "credit score": ["credit_scores", "fico", "FicoScore", "creditScore"],
    "all borrowers": ["borrower_name", "borrowers", "applicants", "new1003Borrowers", "accountHolderNames"],
    "borrower": ["borrower_name", "borrowers", "applicants", "new1003Borrowers", "accountHolderNames"],
    "tri-merge": ["bureaus", "experian", "transunion", "equifax"],
    "three bureaus": ["bureaus", "experian", "transunion", "equifax"],
    "tradeline": ["tradelines", "trade_lines"],
    "payment history": ["tradelines", "payment_history", "mortgage_history"],
    "appraised value": ["value", "appraised_value", "appraisedValue", "marketValue"],
    "property type": ["property_type", "propertyType"],
    "comparable": ["comparables", "comparable_sales"],
    "flood zone": ["flood_zone", "floodZone"],
    "employer": ["employer", "employer_name", "company"],
    "account": ["account_number", "accounts", "accountNumber", "institution", "bank"],
    "account holder": ["account_holder", "accountHolder", "accountHolderNames"],
    "statement period": ["statementPeriodFrom", "statementPeriodTo", "periodStartDate", "periodEndDate"],
    "most recent": ["statementPeriodFrom", "statementPeriodTo", "periodStartDate", "periodEndDate"],
    "months": ["statementPeriodFrom", "statementPeriodTo", "periodStartDate", "periodEndDate"],
    "appraisal date": ["appraisalDate", "appraisal_date"],
    "dated within": ["appraisalDate", "appraisal_date", "dateSigned", "date_signed"],
    "social security": ["ssn", "socialSecurityNumber", "social_security"],
    "lender": ["lender", "lender_name"],
    "expiration": ["expiration_date", "expirationDate", "policy_expiration"],
    "coverage": ["coverage_amount", "coverageAmount", "dwelling_coverage"],
    "policy": ["policy_number", "policyNumber"],
    "legal description": ["legal_description", "legalDescription"],
    "vesting": ["vested_parties", "vesting", "grantee"],
    "liens": ["liens", "encumbrances", "exceptions"],
    "tax year": ["tax_year", "taxYear"],
    "interest rate": ["interest_rate", "interestRate", "note_rate"],
    "loan amount": ["loan_amount", "loanAmount"],
    "prior sale": ["dateOfPriorSaleOrTransfer", "priceOfPriorSaleOrTransfer"],
}


def check_spec_against_manifest(
    spec_text: str,
    extracted_fields: dict,
) -> str | None:
    """
    Check if a specification is satisfied by the manifest's extracted_fields.
    Returns a reason string if satisfied, None otherwise.
    """
    text_lower = spec_text.lower()
    ef_keys_lower = {k.lower(): k for k in extracted_fields}

    for keyword, field_names in SPEC_KEYWORD_TO_FIELDS.items():
        if keyword not in text_lower:
            continue
        for fname in field_names:
            if fname.lower() in ef_keys_lower:
                real_key = ef_keys_lower[fname.lower()]
                val = extracted_fields[real_key]
                if val is not None and val != "" and val != [] and val != {}:
                    return (
                        f"Manifest document contains '{real_key}' confirming this requirement"
                    )
    return None
