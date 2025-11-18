# System Architecture & Data Flow

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WEB BROWSER (User Interface)                 │
│                                                                       │
│  [Dashboard] [Upload Schema] [Upload Script] [Evaluate] [Results]   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP Requests
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FLASK WEB SERVER (Port 5000)                      │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Routes & Controllers (app.py)                                │   │
│  │                                                               │   │
│  │ • Dashboard Routes          • Results Routes                │   │
│  │ • Schema Upload Routes      • Manual Evaluation Routes       │   │
│  │ • Script Upload Routes      • PDF Viewer Routes             │   │
│  │ • Evaluation Routes         • API Endpoints                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ Helper Functions                                              │   │
│  │ • CLI Command Execution     • ObjectId Conversion            │   │
│  │ • MongoDB Operations        • Result Formatting              │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────┬──────────────┬─────────────────────┬──────────────────────┬────┘
     │              │                     │                      │
     │ CLI Calls    │ DB Queries         │ File Uploads         │ API Calls
     ▼              ▼                     ▼                      ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│ CLI Scripts  │ │  MongoDB     │ │  File System │ │ External APIs    │
│              │ │              │ │              │ │                  │
│ • ocr_pdf    │ │ Databases:   │ │ • Uploads/   │ │ • OpenAI         │
│ • scheme_    │ │              │ │ • PDFs       │ │ • Google Gemini  │
│   extractor  │ │ • ai_eval... │ │              │ │                  │
│ • comparator │ │ • schema_db  │ │ static/      │ │                  │
│              │ │ • result_db  │ │ uploads/     │ │                  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘
```

## 📊 Database Collections Diagram

```
MongoDB Cluster
│
├─ ai_evaluation_system (Database)
│  │
│  └─ ocr_extracted_answers (Collection)
│     ├─ _id: ObjectId
│     ├─ examId: ObjectId → references schema_db
│     ├─ studentId: ObjectId
│     ├─ pageNumber: Int
│     ├─ questionNumber: Int
│     ├─ rawText: String (OCR output)
│     ├─ confidence: Float (0-1)
│     ├─ fileName: String
│     └─ createdAt: ISODate
│
├─ schema_db (Database)
│  │
│  └─ schema_extracted_answers (Collection)
│     ├─ _id: ObjectId
│     ├─ examId: ObjectId
│     ├─ professorId: ObjectId
│     ├─ subjectId: ObjectId
│     ├─ rawExtractedText: String
│     ├─ structuredData: Document
│     │  └─ questions: Array of Objects
│     │     ├─ questionNumber: Int
│     │     ├─ questionText: String
│     │     ├─ maxMarks: Int
│     │     ├─ concepts: Array
│     │     └─ evaluationCriteria: Object
│     └─ createdAt: ISODate
│
└─ result_db (Database)
   │
   ├─ evaluations (Collection)
   │  ├─ _id: ObjectId
   │  ├─ examId: ObjectId → references schema_db
   │  ├─ studentId: ObjectId
   │  ├─ perQuestion: Array of Objects
   │  │  ├─ questionNumber: Int
   │  │  ├─ scoredMarks: Int
   │  │  ├─ maxMarks: Int
   │  │  ├─ similarity: Float
   │  │  ├─ ocrConfidenceAvg: Float
   │  │  └─ flags: Array
   │  ├─ overall: Object
   │  │  ├─ totalScoredMarks: Int
   │  │  ├─ totalMaxMarks: Int
   │  │  └─ percentage: Float
   │  └─ generatedAt: ISODate
   │
   └─ manual_evaluations (Collection)
      ├─ _id: ObjectId
      ├─ examId: ObjectId
      ├─ studentId: ObjectId
      ├─ manualMarks: Object
      ├─ notes: String
      └─ evaluatedAt: ISODate
```

## 🔄 Complete Data Flow

```
START: User Action
│
├─ [1] UPLOAD SCHEMA
│  │
│  ├─ User selects PDF from disk
│  ├─ Flask validates: PDF format, size < 100MB
│  ├─ Save to: frontend/static/uploads/TIMESTAMP_filename.pdf
│  │
│  ├─ Execute: scheme_extractor.py <pdf_path> --exam-id <id> ...
│  │  │
│  │  ├─ PyMuPDF opens PDF
│  │  ├─ Extract text (direct or OCR if image)
│  │  │  └─ If image: Send to OpenAI Vision → OCR text
│  │  │
│  │  ├─ Send raw text to GPT-4 + SCHEME_EXTRACTION_PROMPT
│  │  ├─ Parse JSON response
│  │  │  └─ Extract: Questions, Max Marks, Concepts, Criteria
│  │  │
│  │  └─ Store in schema_db.schema_extracted_answers
│  │
│  └─ Return: Exam ID to user
│
├─ [2] UPLOAD SCRIPT
│  │
│  ├─ User provides: Exam ID (from step 1), Student ID
│  ├─ User selects answer script PDF
│  ├─ Flask validates input
│  │
│  ├─ Execute: ocr_pdf.py <pdf_path> --exam-id <id> --student-id <id>
│  │  │
│  │  ├─ For each page in PDF:
│  │  │  ├─ Convert page to image (200 DPI)
│  │  │  ├─ Send to OpenAI Vision API
│  │  │  │  └─ OCR prompt + base64 image
│  │  │  ├─ Extract: Text + Confidence + Question Number
│  │  │  │
│  │  │  └─ Store record in ai_evaluation_system.ocr_extracted_answers
│  │  │     {
│  │  │       examId, studentId, pageNumber, questionNumber,
│  │  │       rawText, confidence, fileName, createdAt
│  │  │     }
│  │
│  └─ Return: Success + Page count
│
├─ [3] RUN EVALUATION
│  │
│  ├─ User provides: Exam ID, Student ID
│  ├─ Flask validates IDs exist
│  │
│  ├─ Execute: comparator.py --exam-id <id> --student-id <id>
│  │  │
│  │  ├─ [3a] Load Data
│  │  │  ├─ Query schema_db for schema → get structured questions
│  │  │  └─ Query ai_evaluation_system for OCR → get student text
│  │  │
│  │  ├─ [3b] For Each Question:
│  │  │  │
│  │  │  ├─ Build reference text from scheme
│  │  │  │  ├─ Question text
│  │  │  │  ├─ Reference answer
│  │  │  │  ├─ Key concepts
│  │  │  │  └─ Must-include points
│  │  │  │
│  │  │  ├─ Aggregate student answer text
│  │  │  │  ├─ Find pages with matching question number
│  │  │  │  ├─ Sort by page number
│  │  │  │  └─ Concatenate text
│  │  │  │
│  │  │  ├─ Generate Embeddings
│  │  │  │  ├─ Send reference text → OpenAI
│  │  │  │  │  └─ model: text-embedding-3-small
│  │  │  │  │  └─ Returns: 1536-d vector
│  │  │  │  │
│  │  │  │  └─ Send student text → OpenAI
│  │  │  │     └─ Returns: 1536-d vector
│  │  │  │
│  │  │  ├─ Calculate Similarity
│  │  │  │  ├─ cosine(reference_vector, student_vector)
│  │  │  │  └─ Returns: 0-1 score
│  │  │  │
│  │  │  ├─ Score Question
│  │  │  │  ├─ scored_marks = round(similarity × max_marks)
│  │  │  │  └─ clamp(scored_marks, 0, max_marks)
│  │  │  │
│  │  │  ├─ Flag Check
│  │  │  │  ├─ If similarity < 0.50: LOW_SIMILARITY
│  │  │  │  ├─ If 0.50 <= similarity < 0.65: BORDERLINE
│  │  │  │  └─ If OCR confidence < 0.55: LOW_OCR_CONFIDENCE
│  │  │  │
│  │  │  └─ Gemini Verification
│  │  │     ├─ Send verification prompt to Gemini
│  │  │     ├─ Includes: student answer, reference, similarity
│  │  │     ├─ Gemini returns: flag + reason + suggested_marks
│  │  │     └─ Add flag if verification returns true
│  │  │
│  │  ├─ [3c] Calculate Overall Score
│  │  │  ├─ total_scored = sum(scored_marks for all questions)
│  │  │  ├─ total_max = sum(max_marks for all questions)
│  │  │  └─ percentage = (total_scored / total_max) × 100
│  │  │
│  │  └─ [3d] Store Result
│  │     └─ Insert to result_db.evaluations:
│  │        {
│  │          examId, studentId, schemeRefId,
│  │          perQuestion: [ { qNum, max, scored, similarity, flags, verification } ],
│  │          overall: { totalMax, totalScored, percentage },
│  │          generatedAt
│  │        }
│  │
│  └─ Return: Result ID to user
│
├─ [4] VIEW RESULTS
│  │
│  ├─ User navigates to Results page
│  ├─ Flask queries result_db.evaluations
│  ├─ Format and display:
│  │  ├─ Overall score circle with percentage
│  │  ├─ Per-question cards with metrics
│  │  ├─ Flagged items highlighted
│  │  └─ Action buttons
│  │
│  └─ Display: Scores, similarity, confidence, flags
│
├─ [5] MANUAL EVALUATION (Optional)
│  │
│  ├─ User clicks "Manual Evaluation" from results
│  ├─ Page loads with auto-generated form
│  │  └─ One input field per question (max to max_marks)
│  │
│  ├─ User:
│  │  ├─ Enters manual marks for each question
│  │  ├─ Adds optional notes
│  │  └─ Clicks Save
│  │
│  ├─ Flask:
│  │  ├─ Validates marks (0 to max_marks)
│  │  └─ Upsert to result_db.manual_evaluations
│  │
│  └─ Return: Success message
│
├─ [6] VIEW OCR TEXT
│  │
│  ├─ User clicks "View Extracted Text"
│  ├─ Flask queries ai_evaluation_system.ocr_extracted_answers
│  │  └─ Filter by examId + studentId, sort by pageNumber
│  │
│  ├─ Display:
│  │  ├─ Page list on left (with question numbers)
│  │  ├─ OCR text in center
│  │  ├─ Confidence scores and controls
│  │  └─ Export buttons
│  │
│  ├─ User interactions:
│  │  ├─ Click page → update text view
│  │  ├─ Zoom In/Out → adjust font size
│  │  ├─ Download → save as .txt
│  │  └─ Copy → copy to clipboard
│  │
│  └─ All operations are client-side (JavaScript)
│
└─ END
```

## 🔗 Component Interaction Diagram

```
                    ┌─────────────────┐
                    │   Flask App     │
                    │    (app.py)     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────────┐   ┌──────────────┐  ┌──────────────────┐
   │   MongoDB   │   │ CLI Scripts  │  │ External APIs    │
   │             │   │              │  │                  │
   │ 3 Databases │   │ • ocr_pdf    │  │ • OpenAI         │
   │ 5 Collections   │ • scheme_ex  │  │   - Vision API   │
   │             │   │ • comparator │  │   - Embeddings   │
   └─────────────┘   │              │  │ • Google Gemini  │
                     └──────────────┘  │                  │
                                       └──────────────────┘

        ┌─────────────────────────────────────────────┐
        │         User Interface (Browser)             │
        │                                              │
        │  Templates + CSS + JavaScript                │
        │  • 9 HTML templates                          │
        │  • Responsive design                         │
        │  • Form validation                           │
        └─────────────────────────────────────────────┘
```

## 📈 Request Flow Timeline

```
Time:    User Action → Framework → Processing → Response
│
├─ T0:   Click "Upload Schema"
├─ T0+:  Page loads (upload_schema.html)
│
├─ T1:   User selects PDF + clicks Submit
├─ T1+:  POST /upload-schema
├─ T1+:  Flask validates file
├─ T1+:  Save file to disk
├─ T1+:  Execute scheme_extractor.py (subprocess)
├─ T1+:  scheme_extractor opens PDF
├─ T1+:  PyMuPDF extracts/OCRs text
├─ T1+:  Send to GPT-4 for structuring
├─ T1+:  Parse JSON response
├─ T1+:  Store in MongoDB (schema_db)
├─ T2:   Return JSON response to Flask
├─ T2+:  Flask returns success + Exam ID
├─ T2+:  JavaScript displays result
├─ T3:   User sees success message + Exam ID
│
(User saves Exam ID)
│
├─ T4:   Click "Upload Script"
├─ T4+:  Page loads (upload_script.html)
├─ T5:   Enter Exam ID + Student ID + select PDF
├─ T6:   POST /upload-script
├─ T6+:  Flask validates
├─ T6+:  Execute ocr_pdf.py
├─ T6+:  For each page: OCR via OpenAI
├─ T6+:  Store results in MongoDB (ai_evaluation_system)
├─ T7:   Return success response
├─ T8:   JavaScript displays success + links
│
├─ T9:   Click "Evaluate"
├─ T9+:  Page loads (evaluate.html)
├─ T10:  Click "Run Evaluation"
├─ T11:  POST /evaluate
├─ T11+: Execute comparator.py
├─ T11+: Load schema from schema_db
├─ T11+: Load OCR from ai_evaluation_system
├─ T11+: Generate embeddings + calculate similarity
├─ T11+: Call Gemini for verification
├─ T11+: Store results in result_db
├─ T12:  Return result ID
├─ T13:  JavaScript redirects to Results page
│
├─ T14:  Results page loads
├─ T14+: GET /results
├─ T14+: Flask fetches from result_db
├─ T14+: Render results.html with data
├─ T15:  User sees scores and metrics
│
└─ T16+: User can: Manual Eval, View OCR, or other actions
```

## 🎯 Error Handling Flow

```
Action → Validation → Processing → Error Check → Response

Valid Path:   ✓ Input → ✓ File → ✓ Processing → Success JSON
Invalid Path: ✗ Input → Error Response (400)
File Path:    ✓ Input → ✗ File → Error Response (400)
Server Path:  ✓ Input → ✓ File → ✗ Processing → Error Response (500)

Errors Returned:
{
  "success": false,
  "message": "Error description"
}

HTTP Codes:
- 200: OK
- 400: Bad Request (validation, file errors)
- 404: Not Found
- 500: Server Error (processing, CLI, API)
```

---

**Architecture Version**: 1.0  
**Last Updated**: November 17, 2025
