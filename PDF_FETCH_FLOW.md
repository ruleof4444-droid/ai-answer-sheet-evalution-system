# PDF/Answer Script Fetch Flow

## Overview
The system fetches and displays answer scripts (PDFs) through two parallel mechanisms:

---

## 1. **Standalone PDF Viewer Page** (`/pdf-viewer`)

### Route: `GET /pdf-viewer`
**Location:** `app.py` line 753

```
User navigates to /pdf-viewer?exam_id=xxx&student_id=yyy
    ↓
Flask renders pdf_viewer.html (line 753-755)
    ↓
HTML loads with form controls for Exam ID & Student ID
```

### Data Fetching Process (pdf_viewer.html)

**User clicks "Load OCR Data" button:**

1. **Extract Input Values**
   ```javascript
   const examId = document.getElementById('exam_id').value;
   const studentId = document.getElementById('student_id').value;
   ```

2. **Fetch from API Route** → `/api/ocr-data/<exam_id>/<student_id>`
   ```javascript
   fetch(`{{ url_for('get_ocr_data', exam_id='', student_id='') }}${examId}/${studentId}`)
   ```

3. **Backend Processing** (app.py line 529-553)
   - Route: `@app.route('/api/ocr-data/<exam_id>/<student_id>', methods=['GET'])`
   - **Database Query:**
     ```python
     pages = list(col_ocr_answers.find(
         {'examId': exam_id, 'studentId': student_id}
     ).sort('pageNumber', 1))
     ```
   - **Database Used:** `ai_evaluation_system.ocr_extracted_answers`
   - **Returns:** JSON with array of pages containing:
     - `page_number`
     - `question_number`
     - `confidence`
     - `text` (raw OCR text)
     - `extracted_at`

4. **Frontend Display**
   - Populates left sidebar with clickable page items
   - Shows OCR extracted text in main viewer area
   - Displays page metadata (Q# and confidence %)

### Features in PDF Viewer
- ✅ Page list with question numbers
- ✅ OCR confidence percentages
- ✅ Zoom in/out on text
- ✅ Copy text to clipboard
- ✅ Download text as `.txt` file

---

## 2. **Results Page Side-by-Side Viewer** (NEW - Added Today)

### Route: `GET /results`
**Location:** `app.py` line 605

```
User views evaluation results
    ↓
results.html renders with two columns:
  - Left: Question cards
  - Right: Answer script viewer
```

### Side-by-Side Data Fetching (results.html JavaScript)

**When page loads:**

1. **Extract Exam & Student IDs from Page Context**
   ```javascript
   const examId = "{{ evaluation.exam_id }}";
   const studentId = "{{ evaluation.student_id }}";
   ```

2. **Fetch PDF Viewer HTML** → `/pdf-viewer?exam_id=xxx&student_id=yyy`
   ```javascript
   fetch(`/pdf-viewer?exam_id=${encodeURIComponent(examId)}&student_id=${encodeURIComponent(studentId)}`)
   ```

3. **Parse Response HTML**
   - Extracts viewer content using CSS selectors:
     - `.pdf-content`
     - `iframe`
     - `img[alt*="PDF"]`
     - `.viewer-main`

4. **Inject into Right Panel**
   ```javascript
   document.getElementById('pdfViewer').innerHTML = viewerContent.outerHTML;
   ```

### Features in Results Page
- ✅ Question-wise evaluation on left
- ✅ Answer script viewer on right (sticky)
- ✅ Side-by-side comparison
- ✅ Responsive (stacks on mobile)
- ✅ Auto-loads when page loads

---

## 3. **Data Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                   Answer Script Fetching                     │
└─────────────────────────────────────────────────────────────┘

SCENARIO A: Standalone Viewer
─────────────────────────────
User → /pdf-viewer?exam_id=X&student_id=Y
           ↓
    renders pdf_viewer.html
           ↓
    User enters IDs or uses provided ones
           ↓
    Clicks "Load OCR Data"
           ↓
    fetch(/api/ocr-data/X/Y)
           ↓
┌─────────────────────────────────┐
│ Backend Route Handler           │
│ get_ocr_data(exam_id, student_id)
│                                 │
│ Query: col_ocr_answers.find()   │
│ Filter: {examId, studentId}     │
│ Sort: by pageNumber             │
└─────────────────────────────────┘
           ↓
    JSON Response:
    {
      success: true,
      data: [
        {
          page_number: 1,
          question_number: 1,
          confidence: 0.92,
          text: "OCR extracted text...",
          extracted_at: "2025-11-18 10:30"
        },
        ...
      ]
    }
           ↓
    Display in UI:
    - Page list (left sidebar)
    - OCR text viewer (main area)


SCENARIO B: Results Page Side-by-Side
──────────────────────────────────────
User → /results?exam_id=X&student_id=Y
           ↓
    renders results.html
           ↓
    JavaScript runs on page load
           ↓
    Extract examId = "{{ evaluation.exam_id }}"
    Extract studentId = "{{ evaluation.student_id }}"
           ↓
    fetch(/pdf-viewer?exam_id=X&student_id=Y)
           ↓
    Receive full pdf_viewer.html page
           ↓
    Parse HTML & extract viewer components
           ↓
    Inject into right panel
           ↓
    Display:
    ┌──────────────────┬─────────────────┐
    │ Questions (Left) │ PDF Viewer(Right)│
    │                  │                 │
    │  Q1: 8/10        │ Page 1          │
    │  Q2: 7/10        │ "OCR text..."   │
    │  Q3: 9/10        │                 │
    │                  │ [Scrollable]    │
    └──────────────────┴─────────────────┘
```

---

## 4. **Database Collections Involved**

### Collection: `ai_evaluation_system.ocr_extracted_answers`

**Sample Document:**
```javascript
{
  _id: ObjectId("..."),
  examId: "exam-123",           // String ID
  studentId: "STU-456",         // String ID
  pageNumber: 1,
  questionNumber: 1,
  fileName: "answer_sheet.pdf",
  confidence: 0.92,
  rawText: "The answer text extracted from OCR...",
  createdAt: ISODate("2025-11-18T10:30:00Z")
}
```

**Query Pattern:**
```javascript
col_ocr_answers.find({
  'examId': exam_id,      // String ID (no conversion needed)
  'studentId': student_id // String ID (no conversion needed)
}).sort('pageNumber', 1)
```

---

## 5. **API Endpoints Summary**

| Endpoint | Method | Purpose | Returns |
|----------|--------|---------|---------|
| `/pdf-viewer` | GET | Renders PDF viewer page | HTML page |
| `/api/ocr-data/<exam_id>/<student_id>` | GET | Fetches OCR text for all pages | JSON array |
| `/api/ocr-text/<exam_id>/<student_id>` | GET | Fetches OCR text for specific page | JSON (single page) |
| `/api/pdf/<filename>` | GET | Serves original PDF file | PDF file |

---

## 6. **Key Implementation Details**

### Location of PDF Viewer HTML
📄 `frontend/templates/pdf_viewer.html` (lines 1-340)

### Location of Results HTML
📄 `frontend/templates/results.html` (now with PDF viewer embedded)

### JavaScript Fetch Logic for Results Page
📍 `results.html` lines 108-128 (newly added script)

### Backend Route Handler
📍 `app.py` line 529-553 (`get_ocr_data` function)

---

## 7. **Data Flow Summary**

1. **No actual PDF files are being "fetched"** in the traditional sense
2. Instead, **OCR-extracted TEXT** is stored in MongoDB and fetched
3. The text is displayed in a viewer UI, not as a PDF image
4. This is more efficient because:
   - Text can be searched, copied, zoomed
   - No need to store large PDF images
   - Faster loading
   - Better accessibility

---

## 8. **Error Handling**

All endpoints include try-catch blocks:

```python
try:
    # Fetch from database
    pages = list(col_ocr_answers.find(...))
except Exception as e:
    logger.error(f"Error fetching OCR data: {e}")
    return jsonify({'success': False, 'message': str(e)}), 500
```

JavaScript also handles errors:
```javascript
.catch(error => {
    console.log('Could not load PDF viewer:', error);
    document.getElementById('pdfViewer').innerHTML = 
        '<p style="color: #999;">Could not load answer script</p>';
});
```

---

## Summary

**Where it fetches from:** MongoDB `ocr_extracted_answers` collection
**How it fetches:** Via `/api/ocr-data/<exam_id>/<student_id>` endpoint
**What it fetches:** OCR-extracted text (not actual PDF)
**Where it displays:** 
- Full page: `/pdf-viewer` 
- Side-by-side: Right panel of `/results`
