# STEP_01 — Specification Evaluator

For each document_request, check if the manifest satisfies its `display.documentation_requirements`.

## How to evaluate

1. Look at each document_request's `display.documentation_requirements` array
2. Find matching documents in the manifest (manifest_docs have `detected_document_type` and `extracted_fields`)
3. For each documentation_requirement, determine if the manifest data confirms it:
   - A requirement about "appraised value" is satisfied if the manifest has a `value` field
   - A requirement about "account holder name" is satisfied if manifest has `accountHolderNames`
   - A requirement about "statement period" is satisfied if manifest has `statementPeriodFrom`/`statementPeriodTo`
   - etc.
4. If NO matching document exists in the manifest for that document_type, all requirements remain unsatisfied

## Tool call

Call `evaluate_specifications` with an evaluations list. For each document_request:
- `document_type`: the document type
- `satisfied_indices`: which documentation_requirements (by 0-based index) are satisfied
- `reasons`: why each is satisfied (one reason per index)

Satisfied requirements get MOVED from `display.documentation_requirements` to `display.satisfied_requirements`.

IMPORTANT:
- Only mark a requirement as satisfied if the manifest clearly has matching data
- Do NOT create new requirements — only transfer existing ones
- If unsure, leave it unsatisfied

Then call `save_step_report`.
