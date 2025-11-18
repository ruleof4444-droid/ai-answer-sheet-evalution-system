# Answer Sheet Evaluation System - Complete User Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Getting Started](#getting-started)
3. [Feature Walkthrough](#feature-walkthrough)
4. [Data Flow](#data-flow)
5. [Common Tasks](#common-tasks)
6. [FAQ](#faq)

## System Overview

The Answer Sheet Evaluation System is an AI-powered platform for automated evaluation of student answer sheets. It combines:

- **OCR Technology**: Extracts text from handwritten answer scripts
- **AI Models**: Uses OpenAI and Google Gemini for intelligent evaluation
- **Semantic Matching**: Compares student answers with marking schemes using embeddings
- **Manual Override**: Allows educators to review and adjust automatic scores

### Key Components

| Component | Purpose | Input | Output |
|-----------|---------|-------|--------|
| **Schema Extractor** | Processes marking schemes | Scheme PDF | Structured questions & criteria |
| **OCR Processor** | Extracts text from scripts | Student script PDF | OCR text with confidence |
| **Comparator** | Scores student answers | Schema + OCR data | Scores, flags, verification |
| **Web Frontend** | User interface | User interactions | Results, analytics |

## Getting Started

### Prerequisites Check
```
✓ Python 3.8+ installed
✓ MongoDB running locally
✓ OpenAI API key
✓ Google API key
✓ PDF files ready (scheme + scripts)
```

### Quick Start (5 minutes)

1. **Start the application**
   ```bash
   cd frontend
   run.bat
   ```
   Opens at http://localhost:5000

2. **Configure environment**
   - Edit `.env` with your API keys
   - Restart the server

3. **Upload marking scheme**
   - Dashboard → Upload Schema
   - Select your scheme PDF
   - Note the displayed Exam ID

4. **Upload student script**
   - Dashboard → Upload Script
   - Enter Exam ID from step 3
   - Enter Student ID
   - Select script PDF

5. **Run evaluation**
   - Dashboard → Evaluate
   - Enter Exam ID and Student ID
   - Click "Run Evaluation"

6. **View results**
   - Dashboard → Results
   - See scores and metrics

## Feature Walkthrough

### 1. Dashboard
**Purpose**: Central hub for system overview and quick access

**What you see**:
- Total exams, evaluations, OCR pages
- Recent evaluation results
- Quick action cards

**Actions**:
- Click any recent evaluation to view details
- Use action cards for quick navigation

---

### 2. Upload Schema
**Purpose**: Load marking schemes into the system

**How it works**:
1. Upload scheme PDF (any format - text or scanned)
2. System extracts text using OCR or direct text extraction
3. AI structures the scheme into:
   - Questions with numbers and text
   - Maximum marks per question
   - Evaluation criteria
   - Key concepts and keywords
   - Reference answers

**Required Information**:
- **Exam ID** (optional): Leave blank for auto-generation
- **Professor ID** (optional): Auto-generated if blank
- **Subject ID** (optional): Auto-generated if blank

**Output**:
- Exam ID (save this!)
- Schema stored in database
- Ready for student evaluations

**Tips**:
- Scheme can be handwritten or printed
- Better OCR confidence = better results
- Save the Exam ID for later use

---

### 3. Upload Script
**Purpose**: Process student answer sheets

**How it works**:
1. Enter Exam ID (from schema upload)
2. Enter Student ID (any unique identifier)
3. Upload student's answer script PDF
4. System:
   - Extracts text using OpenAI Vision API
   - Detects question numbers
   - Calculates OCR confidence
   - Stores all data in database

**OCR Process**:
- Converts PDF pages to high-resolution images
- Sends to OpenAI Vision API
- Extracts text preserving formatting
- Assigns confidence scores (0-1)
- Auto-detects question numbers

**Confidence Scoring**:
- 0.9-1.0: Excellent (clear handwriting)
- 0.7-0.9: Good (mostly clear)
- 0.5-0.7: Fair (some unclear parts)
- <0.5: Poor (very unclear)

**Tips**:
- Clear, legible handwriting improves OCR
- Proper lighting during scanning helps
- Portrait orientation works best
- Can upload multiple scripts per exam

---

### 4. Evaluate
**Purpose**: Run automated scoring on student scripts

**Evaluation Process**:
1. Loads marking scheme
2. Fetches student OCR text
3. For each question:
   - Creates embeddings of reference answer
   - Creates embeddings of student answer
   - Calculates cosine similarity (0-1)
   - Scores = similarity × max_marks
   - Gemini verifies the score
   - Flags suspicious cases

**Similarity Scoring**:
- How similar are the answers? (0-1 scale)
- 0.9+: Nearly identical
- 0.7-0.9: Good match
- 0.5-0.7: Partial match
- <0.5: Poor match

**Flags Generated**:
- **LOW_SIMILARITY**: Score < 50%
- **BORDERLINE_SIMILARITY**: 50-65% similarity
- **LOW_OCR_CONFIDENCE**: OCR < 55%
- **GEMINI_VERIFICATION_FLAG**: AI flagged suspicious

**Preview Feature**:
- Shows schema questions loaded
- Shows OCR pages extracted
- Allows verification before running

---

### 5. Results
**Purpose**: View evaluation scores and details

**Results Display**:

**Overall Score Card**:
- Large percentage circle
- Total marks scored
- Progress bar visualization

**Per-Question Breakdown**:
- Question number
- Scored marks / Max marks
- Similarity score
- OCR confidence
- Gemini suggested marks
- Any flags

**Quality Metrics**:
- Similarity: How well answer matches reference (0-1)
- OCR Confidence: How confident OCR extraction was
- Gemini Marks: AI's suggested mark (may differ from automatic)

**Actions**:
- Manual Evaluation: Override scores
- View Extracted Text: See OCR output
- Back to Results: Return to list

**Tips**:
- Low similarity with high OCR confidence = genuine poor answer
- Low OCR confidence = text extraction was unclear
- Flagged items need manual review
- Compare Gemini marks to automatic marks

---

### 6. Manual Evaluation
**Purpose**: Override automatic scores with human judgment

**When to use**:
- Automatic score seems wrong
- OCR confidence was too low to trust
- Student answer is in different format/language
- Partial credit judgment needed

**How to use**:
1. View a result
2. Click "Manual Evaluation"
3. See automatic scores for reference
4. Enter manual marks for each question
5. Add evaluation notes
6. Save changes

**Marks Input**:
- Enter 0 to max_marks for each question
- Can be partial (e.g., 3.5 out of 5)
- Decimal values supported

**Notes Section**:
- Explain why manual marks differ
- Document special circumstances
- Add grading comments

**Tips**:
- Always reference the OCR text when evaluating
- Use Manual Evaluation for edge cases
- Document your reasoning in notes
- Save provides audit trail

---

### 7. PDF Viewer & OCR Text Display
**Purpose**: Review extracted text from student scripts

**Features**:

**Page Navigation**:
- List all extracted pages
- Show question number per page
- Display OCR confidence per page
- Click to select page

**Text Display**:
- Full extracted text from selected page
- Preserves formatting and line breaks
- Displays original handwriting interpretation

**Controls**:

| Control | Function |
|---------|----------|
| 🔍+ Zoom In | Increase font size +2px |
| 🔍- Zoom Out | Decrease font size -2px |
| ⬇️ Download | Save text as .txt file |
| 📋 Copy | Copy text to clipboard |

**Quality Indicators**:
- Confidence score (0-1 scale)
- Question number detection
- Page count summary

**Tips**:
- Use zoom for better readability
- Compare with original if available
- Check for [?] markers indicating unclear text
- Download for external analysis

## Data Flow

### Complete Workflow

```
START
  ↓
[1. Upload Scheme PDF]
  ├─ Extracted by OCR → Raw Text
  ├─ Structured by AI → Questions, Criteria, Max Marks
  ├─ Stored in schema_db.schema_extracted_answers
  └─ Returns: Exam ID
  ↓
[2. Upload Student Script]
  ├─ Converted to images (200 DPI)
  ├─ Sent to OpenAI Vision API
  ├─ Returns: Extracted Text + Confidence
  ├─ Detects Question Numbers
  ├─ Stored in ai_evaluation_system.ocr_extracted_answers
  └─ Returns: Student ID + Pages Count
  ↓
[3. Run Evaluation]
  ├─ Fetch Scheme from schema_db
  ├─ Fetch OCR Text from ai_evaluation_system
  ├─ For Each Question:
  │   ├─ Build reference text from scheme
  │   ├─ Aggregate student answer text
  │   ├─ Generate embeddings using OpenAI
  │   ├─ Calculate cosine similarity
  │   ├─ Score = similarity × max_marks
  │   ├─ Verify with Gemini
  │   └─ Generate flags if needed
  ├─ Calculate overall percentage
  ├─ Stored in result_db.evaluations
  └─ Returns: Result ID
  ↓
[4. View Results]
  ├─ Fetch from result_db
  ├─ Display scores and metrics
  ├─ Show flagged items
  └─ Offer manual override option
  ↓
[5. Manual Override (Optional)]
  ├─ Update marks
  ├─ Add notes
  ├─ Stored in result_db.manual_evaluations
  └─ Returns: Updated evaluation
  ↓
END
```

### Database Schema

**Schema Collection** (schema_db.schema_extracted_answers)
```json
{
  "_id": ObjectId,
  "examId": ObjectId,
  "professorId": ObjectId,
  "subjectId": ObjectId,
  "pdfMetadata": { ... },
  "rawExtractedText": "...",
  "structuredData": {
    "questions": [
      {
        "questionNumber": 1,
        "questionText": "...",
        "maxMarks": 10,
        "concepts": [...],
        "evaluationCriteria": {...},
        "referenceAnswer": "..."
      }
    ]
  },
  "createdAt": ISODate
}
```

**OCR Collection** (ai_evaluation_system.ocr_extracted_answers)
```json
{
  "_id": ObjectId,
  "examId": ObjectId,
  "studentId": ObjectId,
  "fileName": "...",
  "pageNumber": 1,
  "questionNumber": 1,
  "rawText": "...",
  "confidence": 0.92,
  "createdAt": ISODate
}
```

**Results Collection** (result_db.evaluations)
```json
{
  "_id": ObjectId,
  "examId": ObjectId,
  "studentId": ObjectId,
  "schemeRefId": ObjectId,
  "perQuestion": [
    {
      "questionNumber": 1,
      "maxMarks": 10,
      "scoredMarks": 8,
      "gemini_marks": 8,
      "similarity": 0.87,
      "ocrConfidenceAvg": 0.91,
      "flags": [],
      "verification": {...}
    }
  ],
  "overall": {
    "totalMaxMarks": 100,
    "totalScoredMarks": 82,
    "percentage": 82.0
  },
  "generatedAt": ISODate
}
```

## Common Tasks

### Task 1: Evaluate a Single Student

1. **Prepare**: Have scheme PDF and student script PDF ready
2. **Upload Scheme**: Dashboard → Upload Schema
   - Note the Exam ID
3. **Upload Script**: Dashboard → Upload Script
   - Enter Exam ID
   - Enter Student ID
   - Upload PDF
4. **Evaluate**: Dashboard → Evaluate
   - Enter IDs
   - Click "Run Evaluation"
5. **View**: Dashboard → Results
   - See scores and details

**Time**: ~5-10 minutes

---

### Task 2: Batch Evaluate Multiple Students

1. **Upload Scheme** (once): Dashboard → Upload Schema
   - Note Exam ID
2. **For Each Student**:
   - Upload Script with same Exam ID, different Student ID
   - Run Evaluation
3. **View All Results**: Dashboard → Results
   - See list of all evaluations

**Tip**: Can run all evaluations first, then review results

---

### Task 3: Correct a Wrongly Evaluated Answer

1. **View Result**: Dashboard → Results
2. **Check OCR Text**: Click "View Extracted Text"
   - Verify if student answer was correctly extracted
3. **Review Automatic Score**: Note what system scored
4. **Click Manual Evaluation**
5. **Enter Correct Marks**: Adjust marks per question
6. **Add Notes**: Explain the correction
7. **Save**: Update is recorded

---

### Task 4: Export Evaluation Results

1. **Get PDF Viewer**: Results → View Extracted Text
2. **Download Text**: Click "⬇️ Download"
   - Gets all OCR text
3. **Copy Results**: From Results page
   - Manual copy and paste into Excel/Word

**Note**: No direct export button - use browser "Save Page As" for full HTML

---

### Task 5: Set Up New Exam

1. **Create Folder**: Store scheme and script PDFs
2. **Upload Scheme**: Get and note Exam ID
3. **Create Student List**: Document Student IDs to use
4. **Upload Scripts**: One by one with their IDs
5. **Batch Evaluate**: Run for all students
6. **Review Results**: Check Dashboard → Results

---

## FAQ

**Q: What if the OCR is very poor?**
A: 
- Manual evaluation is your friend
- Use the text viewer to see what was extracted
- Compare with original if available
- Manually override scores with correct values

**Q: Can I re-evaluate a student?**
A:
- Yes, just re-upload the script and run evaluation again
- This creates a new result entry
- Old results are preserved
- Use Manual Evaluation to maintain specific scores

**Q: What do the confidence scores mean?**
A:
- **Similarity (0-1)**: How similar student answer is to reference (cosine of embeddings)
- **OCR Confidence (0-1)**: How confident OCR was in text extraction
- **Percentage (0-100)**: Overall score as percentage

**Q: Why is there a difference between automatic and Gemini marks?**
A:
- Automatic: Based on similarity score alone
- Gemini: AI reviews for context, partial credit, concept presence
- Gemini is sometimes more lenient or strict
- Manual evaluation takes precedence over both

**Q: Can I delete or modify stored data?**
A:
- Currently: No UI for deletion
- For corrections: Use Manual Evaluation
- MongoDB direct access needed for deletion
- Future: May add admin panel with deletion

**Q: What formats of PDFs work best?**
A:
- Clear, high-contrast handwriting
- Portrait orientation
- No shadows or smudges
- Text PDFs (not just scanned images) are easiest
- 200 DPI scans are standard

**Q: How long does evaluation take?**
A:
- OCR: 10-30 seconds per page
- Schema processing: 30-60 seconds
- Evaluation: 1-3 minutes (depends on questions)
- Gemini verification: 10-30 seconds per question

**Q: Is the data secure?**
A:
- Local MongoDB (not cloud)
- No external storage of student data
- API keys in .env (not in code)
- PDFs stored locally

**Q: Can I use my own evaluation criteria?**
A:
- Upload your own marking scheme PDF
- System learns from it
- Modify via manual evaluation if needed
- Future: May add custom evaluation rules

**Q: What about plagiarism detection?**
A:
- Not currently implemented
- Could be added in future
- Would compare student answers across students
- Requires AI model training

**Q: Can teachers/students access the system?**
A:
- Currently: Single-user web access
- Future: Add authentication
- Could limit by exam or student ID
- Role-based permissions possible

---

## Troubleshooting Guide

### Issue: "MongoDB connection failed"
**Solution**:
1. Start MongoDB: `mongod`
2. Check `.env` MONGODB_URL
3. Verify firewall allows localhost:27017

### Issue: "File upload failed"
**Solution**:
1. Check file is actual PDF
2. Verify file < 100MB
3. Ensure `static/uploads` directory writable

### Issue: "No schema found"
**Solution**:
1. Make sure schema was uploaded
2. Check Exam ID is correct
3. Verify using correct Exam ID from upload

### Issue: "OCR extraction very poor"
**Solution**:
1. Check handwriting legibility
2. Rescan with better lighting
3. Use "Manual Evaluation" to fix
4. Consider re-uploading script

### Issue: "Evaluation runs but no results"
**Solution**:
1. Check MongoDB is running
2. Verify schema and OCR data exist
3. Check API keys in `.env`
4. Review application logs for errors

---

## Advanced Tips

### Performance Optimization
- Close unused browser tabs
- Use latest Chrome/Edge for best performance
- Upload one script at a time
- Don't run multiple evaluations simultaneously

### Best Practices
- Always preview data before evaluation
- Review flagged items manually
- Keep Exam ID documented
- Save Student ID list separately
- Backup MongoDB regularly

### Data Organization
- Use consistent naming for Student IDs
- Document exam dates and subjects
- Keep scheme PDFs organized
- Archive old results periodically

---

## Support & Help

**For Technical Issues**:
1. Check README.md in frontend folder
2. Review troubleshooting section above
3. Check application logs (bottom of console)
4. Verify all prerequisites are installed

**For Feature Requests**:
- Document required feature
- Explain use case
- Suggest implementation approach

---

Last Updated: November 2025
Version: 1.0
