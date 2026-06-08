# SBIQ Reevaluator Module

Reevaluates the output of the [Predicted Conditions](https://github.com/antonluisboquer/sbiq-predicted-conditions) pipeline against an updated document manifest. Determines which `display.documentation_requirements` are now satisfied by the manifest and transfers them to `display.satisfied_requirements`.

## Quickstart

```bash
# 1. Clone
git clone https://github.com/antonluisboquer/sbiq-reevaluator-module.git
cd sbiq-reevaluator-module

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up env
cp env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 4. Run
python3 test_pipeline.py --predicted <path/to/final_state.json> --manifest <path/to/manifest.json>
```

## How it works

```
predicted-conditions output ─┐
                             ├──▶ Reevaluator ──▶ Updated document_requests
updated manifest ────────────┘                    (with satisfied_requirements)
```

**3-step pipeline (~60-80s runtime, 8 tool calls):**

| Step | Tool | What it does |
|------|------|--------------|
| STEP_00 | `parse_predicted_conditions` + `parse_manifest` | Parse both inputs into structured state |
| STEP_01 | `evaluate_specifications` | For each doc request, check `display.documentation_requirements` against manifest. Transfer satisfied ones to `display.satisfied_requirements` |
| STEP_02 | `generate_final_output` | Assemble final JSON with updated statuses and stats |

## Inputs

| Input | Format | Description |
|-------|--------|-------------|
| `predicted_conditions_json` | JSON | Output from predicted-conditions (`final_state.json` or `*_output.json`) |
| `updated_manifest_json` | JSON | Document manifest with `documents[]` containing `category.category_name` and `metadata` |

## Output

Same structure as predicted-conditions output, but with:
- `display.satisfied_requirements` — requirements confirmed by the manifest
- `display.documentation_requirements` — only remaining unsatisfied requirements
- `status` updated: `fully_satisfied`, `partially_satisfied`, `satisfied_but_review_required`, or `needed`

## Rules

1. Only **transfers** existing requirements — never creates new ones
2. A requirement is satisfied when the manifest has a matching document with relevant extracted data
3. Blanket aliases (e.g. "Borrower Certification" ↔ "Borrowers Authorization") auto-satisfy all requirements
4. Deterministic keyword-to-field matching supplements LLM evaluation

## LangGraph Cloud

```bash
# Deploy
langgraph up
```

API input:
```json
{
  "predicted_conditions_json": "<raw JSON string>",
  "updated_manifest_json": "<raw JSON string>"
}
```

## Project Structure

```
├── agent.py                  # LangGraph ReAct orchestrator
├── step_loader.py            # Plan/tool resolution per step
├── registry.py               # Auto-generated from config
├── config/
│   ├── workflow_config.json  # Step definitions
│   └── generate.py           # Regenerates registry.py
├── tools/
│   ├── parsing_tools.py      # STEP_00: parse inputs
│   ├── evaluation_tools.py   # STEP_01: evaluate specs against manifest
│   ├── output_tools.py       # STEP_02: generate final output
│   ├── general.py            # save_step_report, get_workflow_status
│   └── shared/
│       └── manifest_matcher.py  # Alias resolution + field matching
├── plans/                    # Per-step markdown prompts
├── langgraph.json            # LangGraph Cloud config
└── test_pipeline.py          # Local E2E runner
```
