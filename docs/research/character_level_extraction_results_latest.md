# Extraction Results Manifest

- status: pass
- scope: extraction-results
- generated_at: 2026-07-02T10:45:41.296864+00:00
- total_files: 66
- unhashed_files: 0
- stored_text_payload_fields: 0
- Heavy OCR: disabled
- macos_vision_available: True
- ocr_backend_policy: prefer_tesseract_else_macos_vision_else_blocked

## Result Counts

- `text_empty`: 17
- `text_extracted`: 49

## Method Counts

- `docx`: 11
- `macos_vision`: 53
- `pdfplumber`: 2

## Post-Extraction Classification Counts

- `extracted_candidate_for_review`: 44
- `extracted_private_reference_only`: 3
- `extracted_reference_only`: 19

## Boundary

Extraction results store text hashes and counts only. Extracted private text is not copied into the repo truth chain.

No extracted text or OCR text is stored in this report; only hashes, counts, methods, and statuses are persisted.
