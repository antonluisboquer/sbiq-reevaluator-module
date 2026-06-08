# STEP_00 — Input Parser

Parse both inputs:
1. Call `parse_predicted_conditions` — extracts document_requests from the predicted-conditions final state
2. Call `parse_manifest` — normalizes the manifest into documents with detected_document_type and extracted_fields

Then call `save_step_report`.
