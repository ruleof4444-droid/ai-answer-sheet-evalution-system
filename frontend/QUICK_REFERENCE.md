# Quick Reference Card

## 🚀 Start the Application

```powershell
cd frontend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Or simply: `run.bat`

Access: **http://localhost:5000**

---

## 📋 Main Workflow

### 1️⃣ Upload Marking Scheme
- **URL**: http://localhost:5000/upload-schema
- **Input**: Scheme PDF + optional IDs
- **Output**: Exam ID (save this!)
- **Time**: 30-60 seconds

### 2️⃣ Upload Student Scripts
- **URL**: http://localhost:5000/upload-script
- **Input**: Exam ID + Student ID + Script PDF
- **Output**: OCR pages stored
- **Time**: 30 seconds to 5 minutes (depends on PDF size)

### 3️⃣ Run Evaluation
- **URL**: http://localhost:5000/evaluate
- **Input**: Exam ID + Student ID
- **Output**: Score and metrics
- **Time**: 1-3 minutes

### 4️⃣ View Results
- **URL**: http://localhost:5000/results
- **Shows**: Scores, similarity, confidence
- **Actions**: Manual override, view OCR

### 5️⃣ Manual Evaluation (if needed)
- **URL**: http://localhost:5000/manual-evaluation
- **Input**: Override marks + notes
- **Output**: Saved manual marks
- **Time**: 5 minutes per student

### 6️⃣ View OCR Text
- **URL**: http://localhost:5000/pdf-viewer
- **Shows**: Extracted text page by page
- **Actions**: Zoom, copy, download
- **Time**: Real-time

---

## 🔑 Key IDs

| ID | Description | Where to Find |
|----|-------------|---------------|
| **Exam ID** | Unique exam identifier | After uploading schema |
| **Student ID** | Unique student identifier | You provide, any format |
| **Result ID** | Result record ID | In results URL |

---

## 📊 Understanding Scores

### Similarity Score (0-1)
- 0.9-1.0: Excellent match
- 0.7-0.9: Good match
- 0.5-0.7: Partial match
- <0.5: Poor match

### Marked Score
- Automatic: `similarity × max_marks` (rounded)
- Gemini: AI suggested score
- Manual: Your override

### Confidence Score
- How sure the OCR was about text extraction
- 0.9-1.0: Very confident
- 0.7-0.9: Confident
- 0.5-0.7: Less confident
- <0.5: Very uncertain

---

## 🎯 MongoDB Commands (for debugging)

```javascript
// Connect to MongoDB
mongo

// Check databases
show dbs

// Switch to evaluation database
use ai_evaluation_system
use schema_db
use result_db

// Count documents
db.ocr_extracted_answers.countDocuments()
db.schema_extracted_answers.countDocuments()
db.evaluations.countDocuments()

// Find all exams
db.schema_extracted_answers.find()

// Find results for exam
db.evaluations.find({ "examId": ObjectId("...") })
```

---

## 🛠️ Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'flask'`
**Solution**: `pip install -r requirements.txt`

### Issue: `MongoDB connection refused`
**Solution**: Start MongoDB: `mongod`

### Issue: `OPENAI_API_KEY not valid`
**Solution**: Check `.env` file has valid key

### Issue: `No schema found`
**Solution**: Upload schema first, use correct Exam ID

### Issue: Poor OCR quality
**Solution**: Use Manual Evaluation to fix scores

### Issue: Page won't load
**Solution**: Try Ctrl+Shift+Del to clear cache

---

## 📁 Important Directories

```
frontend/
├── app.py              ← Main application
├── templates/          ← HTML files
├── static/
│   ├── css/           ← Styles
│   ├── js/            ← JavaScript
│   └── uploads/       ← PDF uploads
└── .env               ← Your config
```

---

## 🔐 Environment Setup

Create `.env` file:
```
MONGODB_URL=mongodb://localhost:27017
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

---

## 💡 Pro Tips

1. **Save Exam IDs**: Write down after uploading scheme
2. **Test First**: Use preview feature before evaluating
3. **Check Flags**: Always review flagged items
4. **Use Manual Eval**: For OCR confidence < 0.5
5. **Backup Data**: Regular MongoDB backups
6. **Clear Cache**: If pages look weird
7. **Use Latest Browser**: Chrome/Edge for best performance
8. **Check Logs**: Bottom of terminal for errors

---

## 📊 Dashboard Quick Stats

**Statistics Shown**:
- Total Exams
- Total Evaluations
- Total OCR Pages
- Recent Evaluations (last 5)

**Quick Actions**:
- Upload Schema
- Upload Script
- Run Evaluation
- View Results

---

## 🔗 Useful Links (When Running)

| Purpose | URL |
|---------|-----|
| Dashboard | http://localhost:5000 |
| Upload Schema | http://localhost:5000/upload-schema |
| Upload Script | http://localhost:5000/upload-script |
| Evaluate | http://localhost:5000/evaluate |
| Results | http://localhost:5000/results |
| Manual Eval | http://localhost:5000/manual-evaluation |
| PDF Viewer | http://localhost:5000/pdf-viewer |

---

## 📱 Mobile Access

From another computer on same network:
```
http://[YOUR_IP]:5000
```

Find your IP:
```powershell
ipconfig
# Look for IPv4 Address
```

---

## 🔄 Data Flow Summary

```
Schema PDF 
    ↓ [ocr_pdf.py]
Structured Scheme (schema_db)
    
Student PDF + Scheme
    ↓ [ocr_pdf.py]
OCR Text (ai_evaluation_system)
    
OCR Text + Scheme
    ↓ [comparator.py]
Scores & Metrics (result_db)
    
Results
    ↓ [Manual Override - Optional]
Final Marks (result_db)
```

---

## ❌ Common Mistakes

❌ **Don't**:
- Upload script before schema
- Use wrong Exam ID for scripts
- Upload non-PDF files
- Try evaluation with no OCR data
- Close browser during uploads
- Skip previewing before evaluation

✅ **Do**:
- Upload schema first
- Note the Exam ID
- Use PDF files
- Check preview data
- Wait for uploads to complete
- Review results carefully
- Use manual eval for edge cases

---

## 📞 When Something Goes Wrong

1. **Check MongoDB**: `mongod` running?
2. **Check .env**: API keys valid?
3. **Check Network**: Can access localhost:5000?
4. **Check Logs**: Read terminal output
5. **Check Uploads**: PDFs in static/uploads/?
6. **Reset**: Clear browser cache, restart app
7. **Reinstall**: `pip install -r requirements.txt --force-reinstall`

---

## 💻 System Requirements

| Component | Requirement |
|-----------|------------|
| **Python** | 3.8+ |
| **MongoDB** | Latest |
| **RAM** | 2+ GB |
| **Disk** | 1+ GB free |
| **Browser** | Chrome/Edge (latest) |
| **Internet** | For API calls (OpenAI, Gemini) |

---

## 📚 Documentation Files

- **README.md**: Technical setup
- **USER_GUIDE.md**: Complete user manual
- **PROJECT_SUMMARY.md**: Project overview
- **This file**: Quick reference

---

**Last Updated**: November 17, 2025  
**Version**: 1.0  
**Status**: ✅ Ready to Use
