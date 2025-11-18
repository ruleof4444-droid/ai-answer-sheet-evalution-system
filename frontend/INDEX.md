# 📚 Frontend Documentation Index

## Start Here! 👇

### 🚀 **First Time Users**
1. Read: **QUICK_REFERENCE.md** (5 min read)
2. Read: **README.md** (10 min read)
3. Install: Follow setup steps in README
4. Start: Run `run.bat` or `python app.py`

### 👥 **End Users (Teachers/Evaluators)**
1. Read: **USER_GUIDE.md** (Complete manual)
2. Start application
3. Follow workflow: Schema → Script → Evaluate → Results

### 👨‍💻 **Developers/Admins**
1. Read: **README.md** (Technical setup)
2. Read: **ARCHITECTURE.md** (System design)
3. Read: **PROJECT_SUMMARY.md** (Code organization)
4. Explore: `app.py` (Main application)

---

## 📖 Documentation Files

### Quick Start
- **QUICK_REFERENCE.md** ⭐
  - Commands and URLs
  - Troubleshooting
  - Pro tips
  - **Read first!** (5 minutes)

### Getting Started
- **README.md**
  - Installation instructions
  - Configuration guide
  - Feature descriptions
  - Troubleshooting guide
  - (15 minutes)

### Complete Guide
- **USER_GUIDE.md**
  - Detailed workflow
  - Each feature explained
  - Common tasks
  - FAQ section
  - (30 minutes)

### Technical Details
- **ARCHITECTURE.md**
  - System architecture
  - Database schema
  - Data flow diagrams
  - Component interactions
  - (20 minutes)

### Project Overview
- **PROJECT_SUMMARY.md**
  - File structure
  - Feature checklist
  - Technology stack
  - (10 minutes)

### Completion Info
- **COMPLETION_SUMMARY.md**
  - What was built
  - Feature list
  - Status and deployment
  - (5 minutes)

---

## 🎯 Quick Navigation by Task

### I want to...

**...start the application**
→ See: QUICK_REFERENCE.md → Start the Application

**...understand how to use it**
→ See: USER_GUIDE.md → Workflow section

**...upload a marking scheme**
→ See: USER_GUIDE.md → Feature Walkthrough → Upload Schema

**...evaluate student scripts**
→ See: USER_GUIDE.md → Common Tasks → Evaluate a Single Student

**...fix a problem**
→ See: QUICK_REFERENCE.md → Troubleshooting OR README.md → Troubleshooting

**...understand the system architecture**
→ See: ARCHITECTURE.md

**...set up the backend**
→ See: README.md → Installation

**...see what features are available**
→ See: PROJECT_SUMMARY.md → Key Features Implemented

**...find an API endpoint**
→ See: README.md → API Endpoints

---

## 📱 Reading by Role

### For Teachers/Evaluators
**Recommended Reading Order**:
1. QUICK_REFERENCE.md (5 min)
2. USER_GUIDE.md → System Overview (5 min)
3. USER_GUIDE.md → Feature Walkthrough (20 min)
4. Start using the system!

### For System Administrators
**Recommended Reading Order**:
1. README.md (15 min)
2. ARCHITECTURE.md (20 min)
3. PROJECT_SUMMARY.md (10 min)
4. Deploy and configure

### For Developers
**Recommended Reading Order**:
1. README.md → Installation (15 min)
2. ARCHITECTURE.md (20 min)
3. PROJECT_SUMMARY.md (10 min)
4. Explore app.py (variable time)
5. Modify as needed

---

## 🔍 Finding Specific Information

| I need to find... | Location |
|-------------------|----------|
| Startup command | QUICK_REFERENCE.md - Start the Application |
| API Key setup | README.md - Configuration |
| Database schema | ARCHITECTURE.md - Database Collections |
| Marking scheme upload steps | USER_GUIDE.md - Feature Walkthrough |
| Troubleshooting errors | README.md or QUICK_REFERENCE.md |
| Feature list | PROJECT_SUMMARY.md or COMPLETION_SUMMARY.md |
| System URLs | QUICK_REFERENCE.md - Useful Links |
| Data flow | ARCHITECTURE.md - Complete Data Flow |
| File structure | PROJECT_SUMMARY.md - Directory Layout |
| Next steps after evaluation | USER_GUIDE.md - Common Tasks |

---

## 📋 File Quick Reference

### Configuration Files
```
.env.example          ← Template for environment variables
requirements.txt      ← Python dependencies
run.bat              ← Windows startup script
```

### Documentation
```
QUICK_REFERENCE.md     ← Start here! (5 min)
README.md             ← Setup guide (15 min)
USER_GUIDE.md         ← Complete manual (30 min)
ARCHITECTURE.md       ← Technical details (20 min)
PROJECT_SUMMARY.md    ← Project overview (10 min)
COMPLETION_SUMMARY.md ← What was built
```

### Application Files
```
app.py                ← Main Flask application
templates/            ← HTML templates (11 files)
static/css/           ← Stylesheets
static/js/            ← JavaScript utilities
```

---

## ✅ Setup Checklist

Use this to ensure everything is ready:

- [ ] Python 3.8+ installed
- [ ] MongoDB running locally
- [ ] Repository cloned/extracted
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with API keys
- [ ] MongoDB connection verified
- [ ] `run.bat` executed
- [ ] Browser opened to localhost:5000
- [ ] Dashboard loaded successfully

---

## 🚨 Common Issues & Solutions

### "Module not found"
→ Run: `pip install -r requirements.txt`

### "MongoDB connection failed"
→ Ensure MongoDB is running: `mongod`

### "API key error"
→ Check `.env` file has valid OpenAI and Google keys

### "No schema found"
→ Upload schema first, then use its Exam ID

### "Poor OCR quality"
→ Use Manual Evaluation to correct scores

### Still stuck?
→ See: QUICK_REFERENCE.md → Troubleshooting

---

## 🎓 Learning Path

**Complete Beginners** (60 minutes total):
1. Read QUICK_REFERENCE.md (5 min)
2. Read README.md (15 min)
3. Install and start app (10 min)
4. Read USER_GUIDE.md (30 min)

**Experienced Users** (15 minutes total):
1. Scan QUICK_REFERENCE.md (5 min)
2. Refer to USER_GUIDE.md as needed (10 min)

**Developers** (60 minutes total):
1. Read README.md (15 min)
2. Read ARCHITECTURE.md (20 min)
3. Explore app.py (15 min)
4. Review PROJECT_SUMMARY.md (10 min)

---

## 💡 Tips

- **Print QUICK_REFERENCE.md** - Keep handy while working
- **Bookmark all documentation** - Easy access
- **Save Exam IDs** - Write them down after schema upload
- **Test with sample** - Use a simple schema first
- **Read FAQ** - USER_GUIDE.md has many answers

---

## 📞 Getting Help

1. **For setup issues** → README.md
2. **For usage questions** → USER_GUIDE.md
3. **For quick lookup** → QUICK_REFERENCE.md
4. **For technical details** → ARCHITECTURE.md
5. **For project info** → PROJECT_SUMMARY.md

---

## 🔗 Quick Links (When App is Running)

- Main App: http://localhost:5000
- Dashboard: http://localhost:5000/
- Upload Schema: http://localhost:5000/upload-schema
- Upload Script: http://localhost:5000/upload-script
- Evaluate: http://localhost:5000/evaluate
- Results: http://localhost:5000/results
- Manual Eval: http://localhost:5000/manual-evaluation
- PDF Viewer: http://localhost:5000/pdf-viewer

---

## 📊 Documentation Statistics

| Document | Lines | Read Time | Purpose |
|----------|-------|-----------|---------|
| QUICK_REFERENCE.md | 300+ | 5 min | Quick lookup |
| README.md | 500+ | 15 min | Setup & config |
| USER_GUIDE.md | 800+ | 30 min | Complete manual |
| ARCHITECTURE.md | 400+ | 20 min | Technical |
| PROJECT_SUMMARY.md | 250+ | 10 min | Overview |
| COMPLETION_SUMMARY.md | 300+ | 5 min | Status |
| **Total** | **2,550+** | **85 min** | Complete |

---

## ✨ Featured Sections

### Most Important
1. QUICK_REFERENCE.md - "Start the Application"
2. USER_GUIDE.md - "Evaluation Workflow"
3. README.md - "Installation"

### Most Useful
1. USER_GUIDE.md - "Common Tasks"
2. USER_GUIDE.md - "FAQ"
3. QUICK_REFERENCE.md - "Troubleshooting"

### Most Technical
1. ARCHITECTURE.md - "Complete Data Flow"
2. ARCHITECTURE.md - "Database Collections"
3. README.md - "API Endpoints"

---

## 🎉 You're All Set!

**Now you can**:
- ✅ Start the application
- ✅ Upload schemas
- ✅ Upload student scripts
- ✅ Run evaluations
- ✅ View results
- ✅ Override scores manually
- ✅ View extracted text

**Questions?** Refer to the documentation!

---

**Happy evaluating! 🚀**

*Last Updated: November 17, 2025*  
*Version: 1.0*
