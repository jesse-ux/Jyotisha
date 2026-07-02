# Extraction Results Manifest

- status: pass
- scope: extraction-results
- generated_at: 2026-07-02T09:44:22.267617+00:00
- total_files: 66
- unhashed_files: 0
- stored_text_payload_fields: 0
- Heavy OCR: disabled

## Result Counts

- `ocr_blocked_missing_engine`: 53
- `text_extracted`: 13

## Method Counts

- `docx`: 11
- `pdfplumber`: 2
- `pytesseract`: 53

## Post-Extraction Classification Counts

- `extracted_candidate_for_review`: 10
- `extracted_private_reference_only`: 3
- `extracted_reference_only`: 53

## Boundary

Extraction results store text hashes and counts only. Extracted private text is not copied into the repo truth chain.

No extracted text or OCR text is stored in this report; only hashes, counts, methods, and statuses are persisted.
