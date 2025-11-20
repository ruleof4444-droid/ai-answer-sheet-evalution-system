# Answer Sheet Evaluation System - Project Prompt

## 🎯 Project Overview

**Answer Sheet Evaluation System** is an AI-powered web application that automates the evaluation of handwritten student answer sheets. The system uses OCR (Optical Character Recognition), natural language processing, and AI models to extract text from handwritten answer sheets, compare them against marking schemes, and generate automated scores with confidence metrics.

## 🏗️ System Architecture

The system consists of three main components:

### 1. **Web Frontend** (`frontend/`)
- **Purpose**: User interface for uploading documents, running evaluations, and viewing results
- **Key Features**:
  - Dashboard with statistics and quick actions
  - Schema (marking scheme) upload interface
  - Student answer script upload interface
  - Evaluation runner with preview capabilities
  - Results display with detailed breakdowns
  - Manual evaluation override system
  - OCR text viewer with page navigation

### 2. **CLI Processing Scripts** (Root directory)
- **`ocr_pdf.py`**: Extracts text from handwritten answer sheet PDFs
- **`scheme_extractor.py`**: Extracts and structures marking scheme PDFs into JSON format
- **`comparator.py`**: Compares student answers with marking schemes using embeddings and AI verification

### 3. **MongoDB Database**
- **Database 1**: `ai_evaluation_system` - Stores OCR extracted text from student scripts
- **Database 2**: `schema_db` - Stores structured marking schemes
- **Database 3**: `result_db` - Stores evaluation results and manual evaluations
- **Database 4**: `exam_management` - Stores exam metadata

## 🔄 Complete Workflow

### Step 1: Upload Marking Scheme
1. User navigates to "Upload Schema" section
2. Uploads a PDF containing the marking scheme/evaluation criteria
3. System calls `scheme_extractor.py` to:
   - Extract text from PDF pages
   - Structure the scheme into JSON format with:
     - Question numbers and text
     - Maximum marks per question
     - Conceptual breakdowns
     - Evaluation criteria
     - Keywords and acceptable variations
4. Structured data stored in `schema_db.schema_extracted_answers`
5. System generates/accepts Exam ID for reference

### Step 2: Upload Student Answer Scripts
1. User navigates to "Upload Script" section
2. Enters Exam ID (from Step 1) and Student ID
3. Uploads student's handwritten answer sheet PDF
4. System calls `ocr_pdf.py` to:
   - Convert PDF pages to images
   - Send images to OCR service
   - Extract handwritten text with confidence scores
   - Detect question numbers automatically
   - Store per-page OCR results in `ai_evaluation_system.ocr_extracted_answers`

### Step 3: Run Evaluation
1. User navigates to "Evaluate" section
2. Enters Exam ID and Student ID
3. System allows preview of:
   - Structured marking scheme
   - OCR extracted text
4. User clicks "Run Evaluation"
5. System calls `comparator.py` to:
   - Load schema and OCR data from MongoDB
   - Generate embeddings for both
   - Calculate cosine similarity scores
   - Use AI verification service
   - Calculate marks based on:
     - Similarity thresholds (low: 0.50, borderline: 0.65, high: 0.85)
     - Conceptual point matching
     - Keyword presence
     - Mandatory concept requirements
   - Flag questionable evaluations (low similarity, low OCR confidence)
   - Store results in `result_db.evaluations`

### Step 4: View Results
1. User navigates to "Results" section
2. System displays:
   - Overall score and percentage
   - Per-question breakdown with:
     - Scored marks vs. maximum marks
     - Similarity scores
     - OCR confidence averages
     - Flags (if any)
   - AI verification status
   - Action buttons for manual evaluation and OCR text viewing

### Step 5: Manual Evaluation (Optional)
1. User can override automatic scores
2. Enter manual marks per question
3. Add evaluation notes
4. Save to `result_db.manual_evaluations`

### Step 6: View OCR Text
1. User can view extracted OCR text page-by-page
2. Download or copy extracted text
3. View confidence scores per page

## 📁 Project Structure

```
answer sheet evaluation system-0.32/
├── frontend/                    # Web application
│   ├── app.py                  # Main application
│   ├── templates/              # UI templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── upload_schema.html
│   │   ├── upload_script.html
│   │   ├── evaluate.html
│   │   ├── results.html
│   │   ├── results_list.html
│   │   ├── manual_evaluation.html
│   │   ├── pdf_viewer.html
│   │   ├── 404.html
│   │   └── 500.html
│   ├── static/
│   │   ├── css/                # Styling files
│   │   ├── js/                 # JavaScript files
│   │   └── uploads/            # Uploaded PDF files
│   ├── requirements.txt         # Dependencies
│   └── [Documentation files]
│
├── ocr_pdf.py                  # OCR extraction script
├── scheme_extractor.py         # Marking scheme extraction script
├── comparator.py              # Evaluation comparison script
└── [Documentation files]
```

## 🔑 Key Features

### Automated Evaluation
- **OCR Extraction**: Handwritten text recognition with confidence scoring
- **Similarity Matching**: Semantic similarity using embeddings
- **AI Verification**: Cross-verification of scores using AI service
- **Conceptual Analysis**: Breaks down answers into conceptual points
- **Keyword Matching**: Identifies important keywords and synonyms
- **Flagging System**: Highlights questionable evaluations for review

### User Interface
- **Dashboard**: Statistics, recent evaluations, quick actions
- **Upload Interfaces**: File upload functionality for PDFs
- **Preview System**: View schema and OCR data before evaluation
- **Results Display**: Score breakdowns, metrics display
- **Manual Override**: Adjust scores manually with notes
- **OCR Viewer**: Page-by-page text viewing with export options

### Data Management
- **MongoDB Integration**: Four databases for different data types
- **ObjectId Handling**: Flexible ID conversion (24-char hex or string hashing)
- **File Management**: Secure PDF uploads with timestamp naming
- **Error Handling**: Comprehensive error pages and API error responses

## ⚙️ Configuration Requirements

### Environment Variables (`.env`)
```env
MONGODB_URL=mongodb://localhost:27017
OPENAI_API_KEY=your_api_key
GOOGLE_API_KEY=your_api_key
```

### Prerequisites
- Python 3.8+
- Database service running and accessible
- OCR service API key
- AI verification service API key

### Installation
1. Navigate to `frontend/` directory
2. Create virtual environment
3. Install dependencies from requirements.txt
4. Create `.env` file with API keys
5. Start MongoDB service
6. Run the application

## 📊 Data Flow

```
User Uploads Schema PDF
    ↓
scheme_extractor.py processes PDF
    ↓
Structured JSON stored in schema_db
    ↓
User Uploads Answer Script PDF
    ↓
ocr_pdf.py extracts text via OCR service
    ↓
OCR text stored in ai_evaluation_system DB
    ↓
User Triggers Evaluation
    ↓
comparator.py:
  - Loads schema and OCR data
  - Generates embeddings
  - Calculates similarity
  - Gets Gemini verification
  - Calculates scores
    ↓
Results stored in result_db
    ↓
User Views Results
    ↓
Optional: Manual Evaluation Override
```

## 🎯 Use Cases

1. **Educational Institutions**: Automated grading of handwritten exams
2. **Exam Centers**: Batch processing of answer sheets
3. **Teachers/Professors**: Quick evaluation with AI assistance
4. **Quality Assurance**: Flagging system for manual review
5. **Analytics**: Score distribution and performance metrics

## 🔒 Security Considerations

- File upload validation (PDF only, size limits)
- Secure filename handling
- Environment variables for API keys
- Database connection timeout
- Input sanitization

## 🚀 Future Enhancements

- User authentication and authorization
- Batch evaluation processing
- Advanced analytics dashboard
- Report generation (PDF/Excel)
- WebSocket for real-time updates
- Redis caching layer
- Mobile app support
- Multiple language support
- Image annotation tools
- Detailed audit logs

## 📝 Key Metrics

- **API Endpoints**: 15+ routes
- **Database Collections**: 4 collections across 4 databases

## 🎓 Understanding the System

### Similarity Scoring
- **Low Similarity** (< 0.50): Flagged for review, likely incorrect
- **Borderline** (0.50-0.65): Partial marks, needs verification
- **High Similarity** (> 0.85): Full marks likely, strong match

### OCR Confidence
- Confidence scores (0-1) indicate OCR accuracy
- Low confidence may affect evaluation reliability
- System flags low-confidence extractions

### Evaluation Criteria
- **Conceptual Points**: Each question broken into concepts
- **Mandatory Concepts**: Must be present for full marks
- **Keywords**: Important terms that must appear
- **Variations**: Acceptable synonyms and phrasings
- **Partial Marks**: Awarded for partial concept coverage

## 🔧 Development Notes

- CLI scripts are called via subprocess from the web application
- MongoDB ObjectIds are used for relationships
- File uploads stored with timestamp prefixes
- Error handling includes 404 and 500 error pages

## 📞 Support & Documentation

- **Quick Start**: `QUICK_REFERENCE.md`
- **User Guide**: `USER_GUIDE.md`
- **Technical Docs**: `README.md`
- **Architecture**: `ARCHITECTURE.md`
- **Project Summary**: `PROJECT_SUMMARY.md`

---

**Version**: 0.32  
**Status**: Production Ready  
**Last Updated**: November 2025  
**License**: Proprietary

