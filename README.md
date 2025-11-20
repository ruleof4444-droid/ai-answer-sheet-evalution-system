# Answer Sheet Evaluation System - Flask Frontend

A comprehensive web-based frontend for the Answer Sheet Evaluation System built with Flask and MongoDB. The system provides automated evaluation of student answer sheets using OCR and AI-powered marking schemes.

## Features

### 🎯 Dashboard
- Overview of system statistics
- Recent evaluations display
- Quick access to all features
- Real-time summary metrics

### 📤 Upload Schema
- Upload marking scheme PDFs
- Automatic scheme extraction and structuring
- Support for complex evaluation criteria
- Schema validation and preview

### 📝 Upload Scripts
- Upload student answer sheet PDFs
- OCR-based text extraction from handwritten answers
- Confidence scoring for OCR accuracy
- Automatic question number detection

### ⚖️ Evaluation
- Automatic script evaluation against marking scheme
- AI-powered verification using Gemini
- Similarity scoring with embeddings
- Flagging of questionable evaluations
- Support for multiple students per exam

### 📊 Results Section
- Detailed evaluation results display
- Question-wise score breakdown
- Similarity and confidence metrics
- Gemini verification status
- Flagged items highlighting

### ✏️ Manual Evaluation
- Override automatic scores with manual marks
- Add evaluation notes
- Per-question mark adjustment
- Support for partial and full marks

### 📄 PDF Viewer & OCR Text Display
- View extracted OCR text from student scripts
- Page-by-page navigation
- Font size adjustment
- Text export and copy functionality
- Confidence score display

## System Architecture

```
frontend/
├── app.py                 # Main Flask application
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── dashboard.html    # Dashboard view
│   ├── upload_schema.html
│   ├── upload_script.html
│   ├── evaluate.html
│   ├── results.html
│   ├── results_list.html
│   ├── manual_evaluation.html
│   ├── pdf_viewer.html
│   ├── 404.html
│   └── 500.html
├── static/
│   ├── css/style.css     # Global styles
│   ├── js/main.js        # Utility functions
│   └── uploads/          # Uploaded PDF files
└── requirements.txt       # Python dependencies
```

## Installation

### Prerequisites
- Python 3.8+
- MongoDB running and accessible
- CLI scripts in parent directory:
  - `ocr_pdf.py` (for OCR extraction)
  - `scheme_extractor.py` (for schema processing)
  - `comparator.py` (for evaluation)

### Setup Steps

1. **Clone/Extract the frontend**
   ```bash
   cd d:\answer sheet evaluation system-0.32\frontend
   ```

2. **Create virtual environment** (optional but recommended)
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the frontend directory:
   ```
   MONGODB_URL=mongodb://localhost:27017
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_API_KEY=your_google_api_key
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

   The application will start at `http://localhost:5000`

## Usage Workflow

### Step 1: Upload Marking Scheme
1. Navigate to "Upload Schema" section
2. Upload a PDF containing the marking scheme
3. Note the generated/provided **Exam ID**
4. System automatically extracts and structures the scheme

### Step 2: Upload Student Scripts
1. Go to "Upload Script" section
2. Enter the **Exam ID** from Step 1
3. Enter a unique **Student ID** for the student
4. Upload the student's answer script PDF
5. System extracts text using OCR and stores in database

### Step 3: Run Evaluation
1. Navigate to "Evaluate" section
2. Enter the Exam ID and Student ID
3. Click "Preview Data" to verify schema and OCR data
4. Click "Run Evaluation" to start scoring
5. System compares student answers with scheme and generates scores

### Step 4: View Results
1. Go to "Results" section
2. Results show:
   - Overall percentage and score
   - Question-wise breakdown
   - Similarity scores
   - OCR confidence metrics
   - Flagged items (if any)

### Step 5: Manual Evaluation (Optional)
1. From results page, click "Manual Evaluation"
2. Override automatic scores with manual marks
3. Add evaluation notes if needed
4. Save manual evaluation

### Step 6: View OCR Text
1. Click "View Extracted Text" from results
2. Browse through pages of extracted text
3. Adjust font size for readability
4. Download or copy extracted text

## API Endpoints

### Dashboard
- `GET /` - Main dashboard

### Schema Management
- `GET/POST /upload-schema` - Upload and process marking scheme
- `GET /api/schema/<exam_id>` - Fetch structured schema

### Script Management
- `GET/POST /upload-script` - Upload and process answer script
- `GET /api/ocr-data/<exam_id>/<student_id>` - Fetch OCR extracted text

### Evaluation
- `GET/POST /evaluate` - Run evaluation
- `GET /results` - View results (list or detail)
- `GET /api/results/<result_id>` - Fetch specific result

### Manual Evaluation
- `GET/POST /manual-evaluation` - Manual evaluation interface
- `GET /api/manual-evaluation/<exam_id>/<student_id>` - Fetch manual eval

### PDF Viewer
- `GET /pdf-viewer` - PDF viewer interface
- `GET /api/ocr-text/<exam_id>/<student_id>` - Get OCR text by page
- `GET /api/pdf/<filename>` - Serve PDF files

## Key Technologies

- **Backend**: Flask
- **Database**: MongoDB
- **AI/ML**: OpenAI (embeddings, GPT), Google Gemini (verification)
- **OCR**: OpenAI Vision API
- **PDF Processing**: PyMuPDF (fitz)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

## Database Collections

### ai_evaluation_system.ocr_extracted_answers
Stores OCR extracted text from student answer sheets

### schema_db.schema_extracted_answers
Stores extracted and structured marking schemes

### result_db.evaluations
Stores evaluation results with scores and metrics

### result_db.manual_evaluations
Stores manual evaluation overrides

## Configuration

### Flask Settings
- `MAX_CONTENT_LENGTH`: 100MB (max file upload size)
- `UPLOAD_FOLDER`: `static/uploads`
- `DEBUG`: True (in development)

### Evaluation Settings
- Similarity thresholds in `comparator.py`
- Embedding model: text-embedding-3-small
- GPT model: gpt-4o-mini

## Error Handling

- 404 errors redirect to dashboard
- 500 errors show server error page
- API errors return JSON with error messages
- Form validation on client and server side

## Security Considerations

- File upload validation (PDF only, 100MB max)
- Secure filename handling
- Environment variables for API keys
- MongoDB connection with timeout
- Input sanitization

## Performance Optimization

- Lazy loading of OCR data
- Database indexing on examId, studentId
- Client-side caching
- Async API calls

## Troubleshooting

### MongoDB Connection Failed
- Ensure MongoDB is running: `mongod`
- Check `MONGODB_URL` in `.env`
- Verify firewall settings

### OCR API Errors
- Verify OpenAI API key is valid
- Check API rate limits
- Ensure sufficient API credits

### Scheme Extraction Failed
- Verify PDF is readable
- Check Google API key configuration
- Ensure proper exam/professor/subject IDs

### File Upload Issues
- Check file is actually PDF format
- Verify file size < 100MB
- Ensure `static/uploads` directory exists and is writable

## Development

### Adding New Features

1. Add route to `app.py`
2. Create HTML template in `templates/`
3. Add JavaScript functionality to `static/js/`
4. Update navigation if needed
5. Test thoroughly with sample data

### Database Queries

Examples for direct MongoDB queries:

```python
# Get schema for exam
schema = col_schema.find_one({'examId': ObjectId(exam_id)})

# Get OCR data
ocr_pages = list(col_ocr_answers.find({'examId': ObjectId(exam_id), 'studentId': ObjectId(student_id)}))

# Get evaluation result
result = col_results.find_one({'examId': ObjectId(exam_id), 'studentId': ObjectId(student_id)})
```

## Future Enhancements

- [ ] User authentication and authorization
- [ ] Batch evaluation processing
- [ ] Advanced analytics dashboard
- [ ] Report generation (PDF/Excel)
- [ ] WebSocket for real-time updates
- [ ] Caching layer (Redis)
- [ ] Mobile app support
- [ ] Multiple language support
- [ ] Image annotation tools
- [ ] Detailed audit logs

## License

Proprietary - Answer Sheet Evaluation System

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review error logs
3. Verify configuration
4. Contact system administrator
