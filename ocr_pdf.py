import sys
import os
import fitz  # PyMuPDF
from pymongo import MongoClient
from datetime import datetime
from openai import OpenAI
import base64
from dotenv import load_dotenv
import re
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "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")

client = OpenAI()

# MongoDB setup
MONGO_URI = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
logger.info(f"🔗 Connecting to MongoDB: {MONGO_URI}")

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()  # Test connection
    logger.info("✅ MongoDB connected successfully")
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    sys.exit(1)

db = mongo_client['ai_evaluation_system']
ocr_collection = db['ocr_extracted_answers']

DETAILED_OCR_PROMPT = """
You are an advanced OCR system specialized in accurately reading handwritten answer sheets.
Extract ALL visible text from the provided page image and follow these instructions carefully:

1. Preserve the exact order, structure, and formatting of the original writing.
2. Maintain all question numbers, bullet points, headings, and sub-headings exactly as written.
3. Retain line breaks, spacing, and paragraph separation for readability.
4. If handwriting is unclear, provide your best interpretation inside [brackets].
5. If a word or part of a word is illegible, write [?] after the uncertain part.
6. Do NOT add or assume new information. Only include what is visible.
7. Include partial/incomplete words exactly as seen.
8. If text is cut off, note "[text cut off]" where appropriate.
9. Keep symbols, diagram labels, and mathematical notations if visible.
10. Do not rewrite or summarize — output the raw extracted text only.

Return the extracted text in plain text format, preserving all original formatting and structure.
At the end of the extracted text, provide a confidence score in the format:
CONFIDENCE_SCORE: <value between 0 and 1>
"""

def validate_id(id_str: str, field_name: str = "ID") -> str:
    """
    Validate and return ID as a string.
    No conversion needed - accepts any string format.
    Users can input exam codes, roll numbers, or any identifier without restriction.
    """
    if not id_str:
        logger.error(f"❌ {field_name} is empty")
        raise ValueError(f"{field_name} cannot be empty")
    
    id_str = str(id_str).strip()
    logger.info(f"✅ {field_name} accepted: {id_str}")
    return id_str

def extract_question_number(text: str) -> int:
    """
    Attempts to detect a question number from the OCR output.
    Returns -1 if not found.
    """
    patterns = [
        r"\bQ(\d+)\b",
        r"\bQuestion\s*(\d+)",
        r"\b(\d+)\)",
        r"\b(\d+)\.",
        r"\b(\d+):"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except:
                pass

    return -1

def extract_text_from_pdf(pdf_path, exam_id=None, student_id=None):
    logger.info("\n" + "="*60)
    logger.info("🔍 OCR EXTRACTION STARTED")
    logger.info("="*60)
    logger.info(f"📄 PDF File: {pdf_path}")
    logger.info(f"🆔 Exam ID: {exam_id}")
    logger.info(f"👤 Student ID: {student_id}")
    
    # Validate and normalize inputs
    try:
        exam_id = validate_id(exam_id, "Exam ID")
        student_id = validate_id(student_id, "Student ID")
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        sys.exit(1)
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        logger.error(f"❌ File not found: {pdf_path}")
        sys.exit(1)
    
    file_size = os.path.getsize(pdf_path) / 1024  # KB
    logger.info(f"📦 File size: {file_size:.2f} KB")
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        logger.info(f"📚 Total pages: {total_pages}")
    except Exception as e:
        logger.error(f"❌ Failed to open PDF: {e}")
        sys.exit(1)
    
    full_text = ""
    last_question_number = -1
    extracted_pages = []

    for i, page in enumerate(doc):
        logger.info(f"\n--- Processing page {i+1}/{total_pages} ---")
        
        try:
            # Convert page to image
            pix = page.get_pixmap(dpi=200)
            image_bytes = pix.tobytes()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            logger.info(f"🖼️  Image size: {len(image_b64)} bytes (base64)")
            
            # Call OpenAI Vision API
            logger.info("🤖 Calling OpenAI Vision API...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You perform precise OCR on handwritten documents."},
                    {"role": "user",
                     "content": [
                         {"type": "text", "text": DETAILED_OCR_PROMPT},
                         {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                     ]}
                ]
            )

            extracted_text = response.choices[0].message.content
            logger.info(f"✅ OCR completed for page {i+1}")
            logger.info(f"📝 Extracted text length: {len(extracted_text)} characters")

            # Extract confidence score
            confidence_score = 0.0
            if "CONFIDENCE_SCORE:" in extracted_text:
                try:
                    confidence_score = float(
                        extracted_text.split("CONFIDENCE_SCORE:")[1].strip().split()[0]
                    )
                    logger.info(f"🎯 Confidence score: {confidence_score}")
                except:
                    logger.warning("⚠️  Could not parse confidence score")

            # Extract question number
            question_number = extract_question_number(extracted_text)
            
            if question_number == -1 and last_question_number != -1:
                question_number = last_question_number
                logger.info(f"📌 Using last question number: {question_number}")
            elif question_number != -1:
                last_question_number = question_number
                logger.info(f"🔢 Detected question number: {question_number}")
            else:
                logger.warning("⚠️  No question number detected")

            # Build record
            record = {
                "examId": exam_id,
                "studentId": student_id,
                "fileName": os.path.basename(pdf_path),
                "pageNumber": i + 1,
                "questionNumber": question_number,
                "rawText": extracted_text,
                "confidence": confidence_score,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }

            # Insert into MongoDB
            result = ocr_collection.insert_one(record)
            logger.info(f"💾 Saved to MongoDB with ID: {result.inserted_id}")
            
            extracted_pages.append({
                'page': i + 1,
                'question': question_number,
                'confidence': confidence_score,
                'text_length': len(extracted_text)
            })

            full_text += extracted_text + "\n\n"
            
        except Exception as e:
            logger.error(f"❌ Error processing page {i+1}: {str(e)}")
            continue

    # Close connections
    doc.close()
    mongo_client.close()
    
    logger.info("\n" + "="*60)
    logger.info("✅ OCR EXTRACTION COMPLETED")
    logger.info("="*60)
    logger.info(f"📊 Summary:")
    logger.info(f"   Total pages processed: {len(extracted_pages)}/{total_pages}")
    logger.info(f"   Total characters extracted: {len(full_text)}")
    
    # Display per-page summary
    logger.info(f"\n📄 Page-wise Summary:")
    for p in extracted_pages:
        logger.info(f"   Page {p['page']}: Q{p['question']}, Confidence: {p['confidence']:.2f}, Length: {p['text_length']} chars")
    
    logger.info("="*60 + "\n")
    
    return full_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract text from PDF using OCR and save to database.")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--exam-id", required=True, help="MongoDB ObjectId for the exam (hex string)")
    parser.add_argument("--student-id", required=True, help="MongoDB ObjectId for the student (hex string)")

    args = parser.parse_args()

    # Convert to absolute path
    pdf_path = os.path.abspath(args.pdf_path)
    
    try:
        result = extract_text_from_pdf(pdf_path, args.exam_id, args.student_id)
        sys.exit(0)  # Success
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {str(e)}")
        sys.exit(1)  # Failure