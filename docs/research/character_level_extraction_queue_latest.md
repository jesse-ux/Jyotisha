# Extraction Queue Manifest

- status: pass
- scope: extraction-queue
- generated_at: 2026-07-02T10:53:47.897123+00:00
- queued_files: 66
- unhashed_files: 0
- Heavy OCR: disabled
- Whole-machine scan: disabled

## Queue Counts

- `document_text_extraction_queued`: 11
- `image_ocr_queued`: 53
- `pdf_text_extraction_queued`: 2

## Source Counts

- `external`: 63
- `project`: 3

## Boundary

Queue only. It identifies PDF/image/document extraction work without performing OCR or promoting extracted text.

Queued files are indexed by path, size, hash, and extraction status only. Private source text is not copied into this report.
