"""
Flask Frontend for Answer Sheet Evaluation System
Integrates with OCR extraction, scheme extraction, and comparison services
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static/uploads')
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# MongoDB setup
MONGO_URI = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
try:
    mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo.server_info()
    logger.info("✅ MongoDB connected successfully")
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")

# Database connections
db_student = mongo["ai_evaluation_system"]
col_ocr_answers = db_student["ocr_extracted_answers"]

db_schema = mongo["schema_db"]
col_schema = db_schema["schema_extracted_answers"]

db_results = mongo["result_db"]
col_results = db_results["evaluations"]

# Exams management database
db_exams = mongo["exam_management"]
col_exams = db_exams["exams"]

# Get parent directory for CLI scripts
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Helper functions
def convert_to_objectid(id_str: str, field_name: str = "ID") -> ObjectId:
    """Safely convert string to MongoDB ObjectId."""
    if not id_str:
        raise ValueError(f"{field_name} cannot be empty")
    
    if len(id_str) == 24:
        try:
            return ObjectId(id_str)
        except:
            pass
    
    # Generate deterministic ObjectId from string
    hash_obj = hashlib.md5(id_str.encode())
    hash_bytes = hash_obj.digest()[:12]
    return ObjectId(hash_bytes)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def run_cli_command(script_name, args):
    """Execute CLI Python scripts."""
    try:
        script_path = os.path.join(PARENT_DIR, script_name)
        cmd = [sys.executable, script_path] + args
        logger.info(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        logger.info(f"Return code: {result.returncode}")
        logger.info(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.error(f"STDERR: {result.stderr}")
        
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False, "", str(e)

# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """Main dashboard."""
    try:
        # Fetch statistics
        total_exams = col_schema.count_documents({})
        total_evaluations = col_results.count_documents({})
        total_ocr_pages = col_ocr_answers.count_documents({})
        
        # Recent evaluations
        recent = list(col_results.find().sort("_id", -1).limit(5))
        
        stats = {
            'total_exams': total_exams,
            'total_evaluations': total_evaluations,
            'total_ocr_pages': total_ocr_pages,
            'recent_evaluations': []
        }
        
        for eval in recent:
            stats['recent_evaluations'].append({
                'id': str(eval['_id']),
                'exam_id': str(eval.get('examId', '')),
                'student_id': str(eval.get('studentId', '')),
                'score': f"{eval['overall']['totalScoredMarks']}/{eval['overall']['totalMaxMarks']}",
                'percentage': eval['overall']['percentage'],
                'created_at': eval.get('generatedAt', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
            })
        
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html', stats={})

# ============================================================================
# EXAM MANAGEMENT ROUTES
# ============================================================================

@app.route('/manage-exams', methods=['GET', 'POST'])
def manage_exams():
    """Manage exams."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            subject_name = data.get('subject_name', '').strip()
            
            if not subject_name:
                return jsonify({'success': False, 'message': 'Subject name is required'}), 400
            
            # Check if exam already exists
            existing = col_exams.find_one({'subject_name': subject_name})
            if existing:
                return jsonify({'success': False, 'message': 'This subject already exists'}), 400
            
            # Create exam with unique ID
            import uuid
            exam_id = str(uuid.uuid4())
            
            exam_doc = {
                'exam_id': exam_id,
                'subject_name': subject_name,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            col_exams.insert_one(exam_doc)
            logger.info(f"Created exam: {subject_name} with ID: {exam_id}")
            
            return jsonify({
                'success': True,
                'message': f'Exam created successfully: {subject_name}',
                'exam_id': exam_id,
                'subject_name': subject_name
            })
        except Exception as e:
            logger.error(f"Error creating exam: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # GET request - return exams list
    try:
        exams = list(col_exams.find().sort('created_at', -1))
        exams_data = [
            {
                'exam_id': str(exam.get('exam_id', '')),
                'subject_name': exam.get('subject_name', ''),
                'created_at': exam.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
            }
            for exam in exams
        ]
        return render_template('manage_exams.html', exams=exams_data)
    except Exception as e:
        logger.error(f"Error fetching exams: {e}")
        return render_template('manage_exams.html', exams=[])

@app.route('/api/exams', methods=['GET'])
def get_exams():
    """Get all exams for dropdown."""
    try:
        exams = list(col_exams.find().sort('subject_name', 1))
        exams_data = [
            {
                'exam_id': str(exam.get('exam_id', '')),
                'subject_name': exam.get('subject_name', '')
            }
            for exam in exams
        ]
        return jsonify({'success': True, 'data': exams_data})
    except Exception as e:
        logger.error(f"Error fetching exams: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/delete-exam/<exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    """Delete an exam."""
    try:
        result = col_exams.delete_one({'exam_id': exam_id})
        
        if result.deleted_count == 0:
            return jsonify({'success': False, 'message': 'Exam not found'}), 404
        
        logger.info(f"Deleted exam: {exam_id}")
        return jsonify({'success': True, 'message': 'Exam deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting exam: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/exam/<exam_id>')
def exam_details(exam_id):
    """View exam details and students."""
    try:
        # Get exam info
        exam = col_exams.find_one({'exam_id': exam_id})
        if not exam:
            return render_template('404.html'), 404
        
        # Get all students for this exam (from OCR collection)
        all_student_ids = col_ocr_answers.distinct('studentId', {'examId': exam_id})
        total_students = len(all_student_ids) if all_student_ids else 0
        
        # Get evaluated students with their results
        evaluated_results = list(col_results.find({'examId': exam_id}).sort('_id', -1))
        evaluated_students_dict = {
            r['studentId']: {
                'student_id': r['studentId'],
                'total_scored': r['overall']['totalScoredMarks'],
                'total_max': r['overall']['totalMaxMarks'],
                'percentage': r['overall']['percentage'],
                'generated_at': r.get('generatedAt', datetime.utcnow()).strftime('%Y-%m-%d %H:%M'),
                'question_count': len(r.get('perQuestion', [])),
                'result_id': str(r['_id'])
            }
            for r in evaluated_results
        }
        
        evaluated_students = set(evaluated_students_dict.keys())
        
        # Get unevaluated students
        unevaluated_students = [s for s in all_student_ids if s not in evaluated_students] if all_student_ids else []
        
        stats = {
            'exam_id': exam_id,
            'subject_name': exam.get('subject_name', ''),
            'total_students': total_students,
            'evaluated_count': len(evaluated_students),
            'unevaluated_count': len(unevaluated_students),
            'unevaluated_students': unevaluated_students,
            'evaluated_students': list(evaluated_students_dict.values())
        }
        
        logger.info(f"Exam details - ID: {exam_id}, Total: {total_students}, Evaluated: {len(evaluated_students)}, Pending: {len(unevaluated_students)}")
        return render_template('exam_details.html', stats=stats)
    except Exception as e:
        logger.error(f"Error fetching exam details: {e}")
        import traceback
        traceback.print_exc()
        return render_template('500.html'), 500

@app.route('/api/batch-evaluate', methods=['POST'])
def batch_evaluate():
    """Batch evaluate selected students."""
    try:
        data = request.get_json()
        exam_id = data.get('exam_id', '')
        student_ids = data.get('student_ids', [])
        
        if not exam_id or not student_ids:
            return jsonify({'success': False, 'message': 'Exam ID and student IDs required'}), 400
        
        results_data = {
            'total': len(student_ids),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        # Evaluate each student one by one
        for student_id in student_ids:
            try:
                logger.info(f"Evaluating {student_id} for exam {exam_id}...")
                
                # Run comparator
                success, stdout, stderr = run_cli_command(
                    'comparator.py',
                    ['--exam-id', exam_id, '--student-id', student_id]
                )
                
                if success:
                    results_data['successful'] += 1
                    logger.info(f"✅ Evaluated {student_id}")
                else:
                    results_data['failed'] += 1
                    results_data['errors'].append({
                        'student_id': student_id,
                        'error': stderr
                    })
                    logger.warning(f"❌ Failed to evaluate {student_id}: {stderr}")
            except Exception as e:
                results_data['failed'] += 1
                results_data['errors'].append({
                    'student_id': student_id,
                    'error': str(e)
                })
                logger.error(f"Error evaluating {student_id}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Batch evaluation complete: {results_data["successful"]} successful, {results_data["failed"]} failed',
            'data': results_data
        })
    except Exception as e:
        logger.error(f"Error in batch evaluation: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/re-evaluate/<exam_id>/<student_id>', methods=['POST'])
def re_evaluate(exam_id, student_id):
    """Re-evaluate a single student."""
    try:
        logger.info(f"Re-evaluating {student_id} for exam {exam_id}...")
        
        # Run comparator
        success, stdout, stderr = run_cli_command(
            'comparator.py',
            ['--exam-id', exam_id, '--student-id', student_id]
        )
        
        if not success:
            logger.warning(f"❌ Failed to re-evaluate {student_id}: {stderr}")
            return jsonify({
                'success': False,
                'message': f'Re-evaluation failed: {stderr}'
            }), 500
        
        # Fetch updated result
        result = col_results.find_one(
            {'examId': exam_id, 'studentId': student_id},
            sort=[('_id', -1)]
        )
        
        if not result:
            return jsonify({'success': False, 'message': 'Result not found'}), 404
        
        logger.info(f"✅ Re-evaluated {student_id}")
        
        return jsonify({
            'success': True,
            'message': 'Re-evaluation completed successfully',
            'data': {
                'student_id': student_id,
                'total_scored': result['overall']['totalScoredMarks'],
                'total_max': result['overall']['totalMaxMarks'],
                'percentage': result['overall']['percentage'],
                'generated_at': result.get('generatedAt', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        logger.error(f"Error re-evaluating: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# UPLOAD SCHEMA ROUTES
# ============================================================================

@app.route('/upload-schema', methods=['GET', 'POST'])
def upload_schema():
    """Upload and process marking scheme PDF."""
    if request.method == 'GET':
        return render_template('upload_schema.html')
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Only PDF files allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"Saved schema PDF: {filepath}")
        
        # Get form data
        exam_id = request.form.get('exam_id') or str(ObjectId())
        professor_id = request.form.get('professor_id') or str(ObjectId())
        subject_id = request.form.get('subject_id') or str(ObjectId())
        
        # Run scheme extraction
        logger.info("Running scheme extraction...")
        success, stdout, stderr = run_cli_command(
            'scheme_extractor.py',
            [filepath, '--exam-id', exam_id, '--professor-id', professor_id, '--subject-id', subject_id]
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': f'Scheme extraction failed: {stderr}'
            }), 500
        
        # Get the stored schema document (use string ID directly)
        schema_doc = col_schema.find_one({'examId': exam_id}, sort=[('_id', -1)])
        
        return jsonify({
            'success': True,
            'message': 'Schema uploaded and processed successfully',
            'exam_id': exam_id,
            'schema_id': str(schema_doc['_id']) if schema_doc else '',
            'file': filename
        })
    
    except Exception as e:
        logger.error(f"Upload schema error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/schema/<exam_id>', methods=['GET'])
def get_schema(exam_id):
    """Fetch schema for a given exam."""
    try:
        # Query using string ID directly
        schema = col_schema.find_one({'examId': exam_id}, sort=[('_id', -1)])
        
        if not schema:
            return jsonify({'success': False, 'message': 'Schema not found'}), 404
        
        structured = json.loads(schema.get('structuredData', '{}'))
        return jsonify({
            'success': True,
            'schema_id': str(schema['_id']),
            'data': structured
        })
    except Exception as e:
        logger.error(f"Error fetching schema: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# UPLOAD SCRIPT ROUTES
# ============================================================================

@app.route('/upload-script', methods=['GET', 'POST'])
def upload_script():
    """Upload and process answer script PDF."""
    if request.method == 'GET':
        return render_template('upload_script.html')
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Only PDF files allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"Saved script PDF: {filepath}")
        
        # Get form data
        exam_id = request.form.get('exam_id', '')
        student_id = request.form.get('student_id', '')
        
        if not exam_id or not student_id:
            return jsonify({'success': False, 'message': 'Exam ID and Student ID required'}), 400
        
        # Run OCR extraction
        logger.info("Running OCR extraction...")
        success, stdout, stderr = run_cli_command(
            'ocr_pdf.py',
            [filepath, '--exam-id', exam_id, '--student-id', student_id]
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': f'OCR extraction failed: {stderr}'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Script uploaded and OCR processed successfully',
            'exam_id': exam_id,
            'student_id': student_id,
            'file': filename
        })
    
    except Exception as e:
        logger.error(f"Upload script error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/ocr-data/<exam_id>/<student_id>', methods=['GET'])
def get_ocr_data(exam_id, student_id):
    """Fetch OCR extracted text for a student."""
    try:
        # Query using string IDs directly
        pages = list(col_ocr_answers.find(
            {'examId': exam_id, 'studentId': student_id}
        ).sort('pageNumber', 1))
        
        ocr_data = []
        for page in pages:
            ocr_data.append({
                'page_number': page.get('pageNumber'),
                'question_number': page.get('questionNumber'),
                'confidence': page.get('confidence', 0),
                'text': page.get('rawText', ''),
                'extracted_at': page.get('createdAt', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'success': True,
            'data': ocr_data,
            'total_pages': len(ocr_data)
        })
    except Exception as e:
        logger.error(f"Error fetching OCR data: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/get-pdf-path/<exam_id>/<student_id>', methods=['GET'])
def get_pdf_path(exam_id, student_id):
    """Get the PDF file path for a student's answer script."""
    try:
        # Query OCR collection to find the PDF filename
        ocr_record = col_ocr_answers.find_one(
            {'examId': exam_id, 'studentId': student_id},
            sort=[('_id', -1)]
        )
        
        if not ocr_record or not ocr_record.get('fileName'):
            return jsonify({'success': False, 'message': 'PDF not found'}), 404
        
        pdf_filename = ocr_record.get('fileName')
        # Return the path to the PDF file
        pdf_path = f"/api/pdf/{secure_filename(pdf_filename)}"
        
        return jsonify({
            'success': True,
            'pdf_path': pdf_path,
            'filename': pdf_filename
        })
    except Exception as e:
        logger.error(f"Error getting PDF path: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/debug/schema-records', methods=['GET'])
def debug_schema_records():
    """Debug endpoint to check schema collection."""
    try:
        records = list(col_schema.find().limit(5))
        debug_data = []
        for rec in records:
            debug_data.append({
                '_id': str(rec.get('_id')),
                'examId': rec.get('examId'),
                'fileName': rec.get('fileName'),
                'filename': rec.get('filename'),
                'file_name': rec.get('file_name'),
                'keys': list(rec.keys())
            })
        
        return jsonify({
            'total_records': col_schema.count_documents({}),
            'sample_records': debug_data
        })
    except Exception as e:
        logger.error(f"Debug error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-schema-pdf-path/<exam_id>', methods=['GET'])
def get_schema_pdf_path(exam_id):
    """Get the PDF file path for an exam's marking scheme."""
    try:
        logger.info(f"Looking for schema PDF for exam_id: {exam_id}")
        
        # Query schema collection to find the PDF filename
        schema_record = col_schema.find_one(
            {'examId': exam_id},
            sort=[('_id', -1)]
        )
        
        if not schema_record:
            logger.warning(f"No schema found with examId={exam_id}")
            return jsonify({'success': False, 'message': 'Schema not found for this exam'}), 404
        
        logger.info(f"Found schema record")
        
        # Try multiple possible field locations for filename
        pdf_filename = None
        
        # Check in pdfMetadata first
        if 'pdfMetadata' in schema_record and isinstance(schema_record['pdfMetadata'], dict):
            pdf_filename = schema_record['pdfMetadata'].get('fileName')
        
        # Fallback to other possible field names
        if not pdf_filename:
            pdf_filename = (schema_record.get('fileName') or 
                          schema_record.get('filename') or 
                          schema_record.get('file_name'))
        
        if not pdf_filename:
            logger.error(f"Schema record has no filename. Keys: {schema_record.keys()}")
            return jsonify({'success': False, 'message': 'No filename in schema record'}), 404
        
        logger.info(f"Using filename: {pdf_filename}")
        
        # Return the path to the PDF file
        pdf_path = f"/api/pdf/{secure_filename(pdf_filename)}"
        
        return jsonify({
            'success': True,
            'pdf_path': pdf_path,
            'filename': pdf_filename
        })
    except Exception as e:
        logger.error(f"Error getting schema PDF path: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# EVALUATION & RESULTS ROUTES
# ============================================================================

@app.route('/evaluate', methods=['GET', 'POST'])
def evaluate():
    """Evaluate student answers."""
    if request.method == 'GET':
        return render_template('evaluate.html')
    
    try:
        exam_id = request.json.get('exam_id', '')
        student_id = request.json.get('student_id', '')
        
        if not exam_id or not student_id:
            return jsonify({'success': False, 'message': 'Exam ID and Student ID required'}), 400
        
        # Run comparator
        logger.info("Running evaluation/comparison...")
        success, stdout, stderr = run_cli_command(
            'comparator.py',
            ['--exam-id', exam_id, '--student-id', student_id]
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': f'Evaluation failed: {stderr}'
            }), 500
        
        # Fetch result (use string IDs directly)
        result = col_results.find_one(
            {'examId': exam_id, 'studentId': student_id},
            sort=[('_id', -1)]
        )
        
        if not result:
            return jsonify({'success': False, 'message': 'Result not found'}), 500
        
        return jsonify({
            'success': True,
            'result_id': str(result['_id']),
            'evaluation': format_evaluation(result)
        })
    
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/results', methods=['GET'])
def results():
    """Display evaluation results."""
    try:
        exam_id = request.args.get('exam_id', '')
        student_id = request.args.get('student_id', '')
        
        if exam_id and student_id:
            # Query using string IDs directly
            result = col_results.find_one(
                {'examId': exam_id, 'studentId': student_id},
                sort=[('_id', -1)]
            )
            
            if result:
                return render_template('results.html', evaluation=format_evaluation(result))
        
        # List all results
        all_results = list(col_results.find().sort('_id', -1).limit(20))
        results_data = [format_evaluation(r) for r in all_results]
        
        return render_template('results_list.html', results=results_data)
    
    except Exception as e:
        logger.error(f"Results error: {e}")
        return render_template('results_list.html', results=[])

@app.route('/api/results/<result_id>', methods=['GET'])
def get_result(result_id):
    """Fetch detailed result."""
    try:
        result = col_results.find_one({'_id': ObjectId(result_id)})
        
        if not result:
            return jsonify({'success': False, 'message': 'Result not found'}), 404
        
        return jsonify({
            'success': True,
            'data': format_evaluation(result)
        })
    except Exception as e:
        logger.error(f"Error fetching result: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def format_evaluation(result):
    """Format evaluation result for frontend."""
    return {
        'id': str(result['_id']),
        'exam_id': str(result.get('examId', '')),
        'student_id': str(result.get('studentId', '')),
        'overall': {
            'total_max': result['overall']['totalMaxMarks'],
            'total_scored': result['overall']['totalScoredMarks'],
            'percentage': result['overall']['percentage']
        },
        'per_question': [
            {
                'question_number': q['questionNumber'],
                'max_marks': q['maxMarks'],
                'scored_marks': q['scoredMarks'],
                'gemini_marks': q.get('gemini_marks', 0),
                'similarity': q['similarity'],
                'ocr_confidence': q['ocrConfidenceAvg'],
                'flags': q.get('flags', []),
                'verification': q.get('verification', {})
            }
            for q in result['perQuestion']
        ],
        'generated_at': result.get('generatedAt', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')
    }

# ============================================================================
# MANUAL EVALUATION ROUTES
# ============================================================================

@app.route('/api/get-evaluation/<exam_id>/<student_id>', methods=['GET'])
def get_evaluation(exam_id, student_id):
    """Fetch evaluation data for manual evaluation comparison."""
    try:
        logger.info(f"Fetching evaluation for exam_id={exam_id}, student_id={student_id}")
        
        # Query the results collection
        result = col_results.find_one(
            {'examId': exam_id, 'studentId': student_id},
            sort=[('_id', -1)]
        )
        
        if not result:
            logger.warning(f"No evaluation found for exam_id={exam_id}, student_id={student_id}")
            return jsonify({'success': False, 'message': 'Evaluation not found - please evaluate this student first'}), 404
        
        logger.info(f"Found evaluation, processing data...")
        
        # Format and return the data
        evaluation_data = {
            'overall': {
                'total_max': result['overall'].get('totalMaxMarks', 0),
                'total_scored': result['overall'].get('totalScoredMarks', 0),
                'percentage': result['overall'].get('percentage', 0)
            },
            'per_question': [
                {
                    'question_number': q.get('questionNumber'),
                    'max_marks': q.get('maxMarks', 0),
                    'scored_marks': q.get('scoredMarks', 0),
                    'similarity': q.get('similarity', 0),
                    'ocr_confidence': q.get('ocrConfidenceAvg', 0),
                    'flags': q.get('flags', []),
                }
                for q in result.get('perQuestion', [])
            ]
        }
        
        logger.info(f"Returning evaluation data: {len(evaluation_data['per_question'])} questions")
        
        return jsonify({
            'success': True,
            'data': evaluation_data
        })
    except Exception as e:
        logger.error(f"Error fetching evaluation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/manual-evaluation', methods=['GET', 'POST'])
def manual_evaluation():
    """Manual evaluation interface."""
    if request.method == 'GET':
        exam_id = request.args.get('exam_id', '')
        student_id = request.args.get('student_id', '')
        return render_template('manual_evaluation.html', exam_id=exam_id, student_id=student_id)
    
    try:
        data = request.json
        exam_id = data.get('exam_id', '')
        student_id = data.get('student_id', '')
        manual_marks = data.get('manual_marks', {})
        notes = data.get('notes', '')
        
        if not exam_id or not student_id:
            return jsonify({'success': False, 'message': 'Exam ID and Student ID required'}), 400
        
        # Save manual evaluation to database
        manual_eval = {
            'examId': exam_id,
            'studentId': student_id,
            'manualMarks': manual_marks,
            'notes': notes,
            'evaluatedAt': datetime.utcnow(),
            'evaluatedBy': 'manual'
        }
        
        # Insert or update in manual evaluations collection
        col_manual = db_results['manual_evaluations']
        result = col_manual.update_one(
            {'examId': exam_id, 'studentId': student_id},
            {'$set': manual_eval},
            upsert=True
        )
        
        # Now update the main results collection with manual marks
        logger.info(f"Updating main results with manual marks for {exam_id}/{student_id}")
        
        # Fetch the current evaluation
        current_result = col_results.find_one({
            'examId': exam_id,
            'studentId': student_id
        })
        
        if current_result:
            # Update per-question marks with manual overrides
            updated_per_question = current_result.get('perQuestion', [])
            total_manual_scored = 0
            total_max = 0
            
            for question in updated_per_question:
                q_num = question.get('questionNumber')
                # Check if there's a manual override for this question
                manual_mark_key = f'q{q_num}'
                
                if manual_mark_key in manual_marks:
                    manual_mark = float(manual_marks[manual_mark_key])
                    question['scoredMarks'] = manual_mark
                    question['isManualOverride'] = True
                    logger.info(f"Updated Q{q_num} manual mark: {manual_mark}")
                
                total_manual_scored += question.get('scoredMarks', 0)
                total_max += question.get('maxMarks', 0)
            
            # Calculate new percentage
            new_percentage = int((total_manual_scored / total_max * 100)) if total_max > 0 else 0
            
            # Update the overall section
            overall_update = {
                'totalScoredMarks': total_manual_scored,
                'percentage': new_percentage
            }
            
            # Update the main results collection
            col_results.update_one(
                {'examId': exam_id, 'studentId': student_id},
                {
                    '$set': {
                        'perQuestion': updated_per_question,
                        'overall': {**current_result['overall'], **overall_update},
                        'updatedAt': datetime.utcnow(),
                        'evaluationMethod': 'manual_override'
                    }
                }
            )
            
            logger.info(f"Updated main results: {total_manual_scored}/{total_max} ({new_percentage}%)")
        else:
            logger.warning(f"No main evaluation found for {exam_id}/{student_id}")
        
        return jsonify({
            'success': True,
            'message': 'Manual evaluation saved and results updated successfully',
            'id': str(result.upserted_id) if result.upserted_id else 'updated'
        })
    
    except Exception as e:
        logger.error(f"Manual evaluation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/manual-evaluation/<exam_id>/<student_id>', methods=['GET'])
def get_manual_evaluation(exam_id, student_id):
    """Fetch manual evaluation."""
    try:
        col_manual = db_results['manual_evaluations']
        manual = col_manual.find_one({'examId': exam_id, 'studentId': student_id})
        
        if not manual:
            return jsonify({'success': True, 'data': None})
        
        return jsonify({
            'success': True,
            'data': {
                'id': str(manual['_id']),
                'manual_marks': manual.get('manualMarks', {}),
                'notes': manual.get('notes', ''),
                'evaluated_at': manual.get('evaluatedAt', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')
            }
        })
    except Exception as e:
        logger.error(f"Error fetching manual evaluation: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# PDF VIEWER ROUTES
# ============================================================================

@app.route('/pdf-viewer', methods=['GET'])
def pdf_viewer():
    """PDF viewer interface."""
    exam_id = request.args.get('exam_id', '')
    student_id = request.args.get('student_id', '')
    return render_template('pdf_viewer.html', exam_id=exam_id, student_id=student_id)

@app.route('/api/ocr-text/<exam_id>/<student_id>', methods=['GET'])
def get_ocr_text(exam_id, student_id):
    """Get OCR extracted text by page."""
    try:
        page_num = request.args.get('page', 1, type=int)
        
        page = col_ocr_answers.find_one({
            'examId': exam_id,
            'studentId': student_id,
            'pageNumber': page_num
        })
        
        if not page:
            return jsonify({'success': False, 'message': 'Page not found'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'page_number': page.get('pageNumber'),
                'question_number': page.get('questionNumber'),
                'confidence': page.get('confidence', 0),
                'text': page.get('rawText', ''),
                'file_name': page.get('fileName', '')
            }
        })
    except Exception as e:
        logger.error(f"Error fetching OCR text: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# FLAGGED ANSWERS ROUTES
# ============================================================================

@app.route('/flagged-answers', methods=['GET'])
def flagged_answers():
    """Display page with all flagged answers."""
    return render_template('flagged_answers.html')

@app.route('/api/flagged-answers', methods=['GET'])
def get_flagged_answers():
    """Get all flagged questions from all evaluations."""
    try:
        exam_id = request.args.get('exam_id', None)
        student_id = request.args.get('student_id', None)
        
        # Build query
        query = {}
        if exam_id:
            query['examId'] = exam_id
        if student_id:
            query['studentId'] = student_id
        
        # Get all results
        all_results = list(col_results.find(query).sort('_id', -1))
        
        flagged_items = []
        for result in all_results:
            exam_id_val = result.get('examId', '')
            student_id_val = result.get('studentId', '')
            result_id = str(result['_id'])
            
            for question in result.get('perQuestion', []):
                flags = question.get('flags', [])
                if flags:  # Only include questions with flags
                    flagged_items.append({
                        'result_id': result_id,
                        'exam_id': exam_id_val,
                        'student_id': student_id_val,
                        'question_number': question.get('questionNumber'),
                        'max_marks': question.get('maxMarks', 0),
                        'scored_marks': question.get('scoredMarks', 0),
                        'gemini_marks': question.get('gemini_marks', 0),
                        'similarity': question.get('similarity', 0),
                        'ocr_confidence': question.get('ocrConfidenceAvg', 0),
                        'flags': flags,
                        'verification': question.get('verification', {}),
                        'generated_at': result.get('generatedAt', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        return jsonify({
            'success': True,
            'data': flagged_items,
            'count': len(flagged_items)
        })
    except Exception as e:
        logger.error(f"Error fetching flagged answers: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/remove-flag', methods=['POST'])
def remove_flag():
    """Intelligently remove a flag from a question."""
    try:
        data = request.json
        exam_id = data.get('exam_id')
        student_id = data.get('student_id')
        question_number = data.get('question_number')
        flags_to_remove = data.get('flags_to_remove', [])  # List of specific flags to remove
        
        if not exam_id or not student_id or not question_number:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Get the current result
        result = col_results.find_one({
            'examId': exam_id,
            'studentId': student_id
        }, sort=[('_id', -1)])
        
        if not result:
            return jsonify({'success': False, 'message': 'Result not found'}), 404
        
        # Find the question and check if flags still apply
        updated_per_question = []
        flag_removed = False
        removed_flags = []
        remaining_flags = []
        
        for question in result.get('perQuestion', []):
            if question.get('questionNumber') == question_number:
                current_flags = question.get('flags', [])
                
                if flags_to_remove:
                    # Remove specific flags
                    remaining_flags = [f for f in current_flags if f not in flags_to_remove]
                    removed_flags = [f for f in current_flags if f in flags_to_remove]
                else:
                    # Remove all flags (if user confirms)
                    remaining_flags = []
                    removed_flags = current_flags.copy()
                
                # Intelligent flag removal: Check if conditions still warrant flags
                if remaining_flags != current_flags:
                    # Store removed flags in a new field for audit trail
                    question['flags'] = remaining_flags
                    question['flagsHistory'] = question.get('flagsHistory', [])
                    question['flagsHistory'].append({
                        'removed_flags': removed_flags,
                        'removed_at': datetime.utcnow(),
                        'reason': data.get('reason', 'Manual removal')
                    })
                    flag_removed = True
                
                updated_per_question.append(question)
            else:
                updated_per_question.append(question)
        
        if not flag_removed:
            return jsonify({
                'success': False,
                'message': 'No flags were removed. Flags may have already been removed or do not exist.'
            }), 400
        
        # Update the result in database
        col_results.update_one(
            {'_id': result['_id']},
            {
                '$set': {
                    'perQuestion': updated_per_question,
                    'updatedAt': datetime.utcnow()
                }
            }
        )
        
        removed_count = len(removed_flags)
        logger.info(f"Removed {removed_count} flag(s) from Q{question_number} for {exam_id}/{student_id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully removed {removed_count} flag(s)',
            'remaining_flags': remaining_flags,
            'removed_flags': removed_flags
        })
    
    except Exception as e:
        logger.error(f"Error removing flag: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/pdf/<filename>')
def serve_pdf(filename):
    """Serve uploaded PDF files."""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='application/pdf')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error serving PDF: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# DELETE ROUTES
# ============================================================================

@app.route('/api/delete-script/<exam_id>/<student_id>', methods=['DELETE'])
def delete_script(exam_id, student_id):
    """Delete answer script and associated data."""
    try:
        # Delete from OCR collection
        col_ocr_answers.delete_many({
            'examId': exam_id,
            'studentId': student_id
        })
        
        # Delete from results collection
        col_results.delete_many({
            'examId': exam_id,
            'studentId': student_id
        })
        
        # Delete from manual evaluations collection if exists
        try:
            col_manual = db_results['manual_evaluations']
            col_manual.delete_many({
                'examId': exam_id,
                'studentId': student_id
            })
        except:
            pass
        
        logger.info(f"Deleted script data for exam_id={exam_id}, student_id={student_id}")
        
        return jsonify({
            'success': True,
            'message': f'Script for {student_id} deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting script: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=True, host='0.0.0.0', port=5000)
