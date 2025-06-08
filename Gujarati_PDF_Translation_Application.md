# Gujarati PDF Translation Application – Research Report

## 1. Introduction  
The goal is to build a web application that enables users to upload Gujarati‐language PDF documents and receive back a translated PDF (e.g., in English) that closely mirrors the original’s layout and structural elements. This addresses the manual, error-prone, and costly process currently faced by legal professionals and others who work with multilingual legal content (PRD.md §1.1).

---

## 2. Core Workflow Overview  

1. **PDF Upload** (client → server)  
2. **Accurate Text + Structure Extraction** (server side)  
3. **Prepare Structured Content for Translation** (intermediate format)  
4. **Translate via Sarvam AI** (chunking & structure preservation)  
5. **Generate Translated PDF** (re-apply styling/layout)  
6. **Serve Download to User**

---

## 3. Detailed Steps and Technical Considerations  

### 3.1 PDF Upload  
| Aspect | Notes |
|--------|-------|
| Front-end | Simple HTML `<form>` with `<input type="file">`; show progress bar for large files. |
| Back-end | Flask (Python) `@app.route('/upload', methods=['POST'])`; save file to `/tmp` or a configurable uploads directory (`legalai` currently uses `src/static/uploads/`). |
| Storage | Temporary file system storage; delete after successful translation or after a TTL to conserve space. |

### 3.2 Accurate Text and Structure Extraction (Gujarati PDFs)  
**Challenges**  
* PDFs are presentation-oriented; logical reading order and styling are not explicit.  
* Scanned PDFs require OCR; digital PDFs may still embed fonts that complicate Unicode extraction.  

**Tools & Libraries**  
| Requirement | Candidate Library | Rationale / Capabilities |
|-------------|------------------|--------------------------|
| Parse selectable text & basic geometry | `pdfplumber`, `pdfminer.six` | Extract text boxes with x-y coordinates, font size, etc. |
| Handle encrypted or tricky layouts | `PyPDF2` (fallback) | Basic text extraction, metadata. |
| OCR for scanned pages | `pytesseract` (Gujarati traineddata) + `pdf2image` | Converts page to image → OCR; accuracy hinges on clean scans and correct DPI. |
| Unified pipeline | `multilingual-pdf2text` (cited in PRD) | Wraps miner/OCR; returns Markdown with structure hints. |

**Extracting Structure & Style**  
* Capture: paragraph boundaries, headings (larger/bold fonts), lists, table cell coordinates, images placeholders.  
* Store as an intermediate representation (Markdown or HTML with CSS classes).  
* Keep mapping between original page number / location and extracted chunk for later reassembly.

### 3.3 Preparing Content for Translation  
* Convert extracted content to **HTML** (preferred) or structured Markdown:  
  ```html
  <p>...</p>
  <h2>...</h2>
  <table>...</table>
  ```  
* Embed style hints (e.g., class names, `<b>`, `<i>`) so Sarvam keeps tags intact.  
* Chunking strategy:  
  * Split by top-level blocks (paragraph, list item, table row) rather than arbitrary characters.  
  * Ensure each chunk ≤ 1000 characters (Sarvam API limit), include opening & closing tags in each chunk to avoid broken markup.  
  * Maintain an ordered manifest to later concatenate.

### 3.4 Translation using Sarvam AI  
* Endpoint: `POST /translate` (Sarvam docs).  
* Request body:  
  ```json
  {
    "text": "<p>Gujarati text...</p>",
    "source_language": "gu",
    "target_language": "en"
  }
  ```  
* Expected behavior: Sarvam-Translate preserves inline HTML/LaTeX/code, translating only human-readable content (blog example: HTML & LaTeX preserved).  
* API limits & throughput: parallelise up to RPS quota; implement exponential back-off.  
* Re-assemble translated chunks in original order to get full HTML document.

### 3.5 Generating Translated PDF with Preserved Formatting  
**Conversion libraries**  
| Library | Strengths | Caveats |
|---------|-----------|---------|
| `WeasyPrint` | CSS 2.1/3 support, good for complex layouts, Unicode; used in `legalai` repository. | Larger dependency stack, some CSS not supported. |
| `xhtml2pdf` | Lightweight, easy install. | Limited CSS, may break complex layouts. |
| `wkhtmltopdf` | WebKit engine, excellent page fidelity. | External binary, heavier deployment. |

**Style Re-application Strategy**  
1. Pass translated HTML into chosen renderer.  
2. Apply CSS generated from original font size/weight mapping (captured in 3.2).  
3. Preserve page breaks by inserting `<div style="page-break-after:always">` where original pages ended.  
4. For tables/lists, use same column widths & list styles obtained from extraction geometry.  

**Limitations**  
* Complex, highly designed PDFs (multi-column, anchored images) may not reproduce perfectly.  
* Goal: **functional equivalence** – legal meaning and general layout preserved even if micro-spacing differs.

### 3.6 User Download of Translated PDF  
* Flask route `@app.route('/download/<file_id>')` with `send_from_directory`.  
* Set `Content-Disposition: attachment; filename="translated_<orig>.pdf"`.  
* Optionally show link immediately after processing or email the file if long-running job.

---

## 4. Key Challenges Revisited  
1. **Gujarati OCR Accuracy** – requires high-quality scans and fine-tuned Tesseract config; consider language-specific preprocessing (deskew, binarise).  
2. **Complex Formatting & Layout Preservation** – extraction and regeneration are lossy; invest in geometric analysis and CSS mapping.  
3. **Maintaining Context Across Chunks** – ensure paragraphs are not split mid-sentence; include minimal context tags or overlap when necessary.  

---

## 5. Role of Sarvam AI  

| Aspect | Sarvam AI Contribution |
|--------|-----------------------|
| Translation Quality | Domain-aware model (Sarvam-Translate) shows superior performance vs. generic LLMs for Indian languages (blog comparisons). |
| Structure Handling | Proven ability to keep HTML, LaTeX, SRT timing intact during translation. |
| Non-roles | Does **not** perform PDF parsing/OCR or PDF creation; these remain application responsibilities. |

---

## 6. Conclusion  
Building a Gujarati PDF translation app that **uploads → extracts → translates → reconstructs PDF** is feasible with existing open-source tooling complemented by Sarvam AI for language conversion.

* **Extraction & Reconstruction** are the hardest engineering pieces; combine text-geometry capture with HTML/CSS rendering to reach “visually similar” fidelity.  
* **Sarvam AI** excels at translating structured HTML while preserving tags, reducing post-processing effort.  
* With careful chunking, style mapping, and robust OCR fallback, the application can significantly cut manual translation time for legal professionals, aligning with objectives outlined in `PRD.md` and the `legalai` codebase design.