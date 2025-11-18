import os, sys, json, argparse, logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any, List
import google.generativeai as genai
from dotenv import load_dotenv
from pymongo import MongoClient
import numpy as np
from openai import OpenAI
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# API Keys
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "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")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyBF5Hk89mLP41L2xlmquCoLjY8zJ0MkTLY"))

# Config
MONGO_URI = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
EMBED_MODEL = "text-embedding-3-small"
LOW_SIMILARITY_FLAG = 0.50
BORDERLINE_SIMILARITY = 0.65
HIGH_SIMILARITY = 0.85

# MongoDB
logger.info(f"🔗 Connecting to MongoDB: {MONGO_URI}")
try:
    mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo.server_info()
    logger.info("✅ MongoDB connected successfully")
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    sys.exit(1)

db_student = mongo["ai_evaluation_system"]
col_student = db_student["ocr_extracted_answers"]

db_schema = mongo["schema_db"]
col_schema = db_schema["schema_extracted_answers"]

db_results = mongo["result_db"]
col_results = db_results["evaluations"]

# OpenAI client
client = OpenAI()

# Helper functions
def validate_id(id_str: str, field_name: str = "ID") -> str:
    """
    Validate and return ID as a string.
    Accepts any string format without ObjectId conversion.
    """
    if not id_str:
        logger.error(f"❌ {field_name} is empty")
        raise ValueError(f"{field_name} cannot be empty")
    
    id_str = str(id_str).strip()
    logger.info(f"✅ {field_name} validated: {id_str}")
    return id_str

def safe_json_loads(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        cleaned = text.strip().strip("`").strip("json").strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"questions": [], "metadata": {}}

def cosine(a: List[float], b: List[float]) -> float:
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))

def embed(texts: List[str]) -> List[List[float]]:
    logger.info(f"🔤 Generating embeddings for {len(texts)} texts...")
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    logger.info(f"✅ Embeddings generated")
    return [d.embedding for d in resp.data]

def build_reference_text(q: Dict[str, Any]) -> str:
    parts = [
        q.get("questionText", ""),
        q.get("referenceAnswer", ""),
        " ".join(q.get("evaluationCriteria", {}).get("mustIncludePoints", []) or []),
        q.get("evaluationCriteria", {}).get("fullMarksRequirements", "") or "",
    ]
    
    concept_bits = []
    for c in q.get("concepts", []) or []:
        concept_bits.append(c.get("description", ""))
        kws = c.get("keywords", []) or []
        if isinstance(kws, list):
            concept_bits.append(" ".join(kws))
    parts.append(" ".join(concept_bits))
    
    ref = "\n".join([p for p in parts if p and isinstance(p, str)])
    return ref if ref.strip() else q.get("questionText", "")

def aggregate_student_answers(pages: List[Dict[str, Any]]) -> str:
    pages_sorted = sorted(pages, key=lambda x: x.get("pageNumber", 0))
    return "\n".join(p.get("rawText", "") for p in pages_sorted)

def flags_for(similarity: float, ocr_conf_avg: float) -> List[str]:
    flags = []
    if similarity < LOW_SIMILARITY_FLAG:
        flags.append("LOW_SIMILARITY")
    elif LOW_SIMILARITY_FLAG <= similarity < BORDERLINE_SIMILARITY:
        flags.append("BORDERLINE_SIMILARITY")
    if ocr_conf_avg and ocr_conf_avg < 0.55:
        flags.append("LOW_OCR_CONFIDENCE")
    return flags

def verify_with_gemini(question_number: int, student_text: str, reference_text: str,
                       scored_marks: int, similarity: float, ocr_confidence: float,
                       max_marks: int) -> Dict[str, Any]:
    
    if not student_text.strip():
        return {
            "verificationFlag": True,
            "reason": "Empty or missing student answer.",
            "gemini_marks": 0
        }

    prompt = f"""
You are an exam evaluation verification AI.
Your role is to verify whether the automatic score seems reasonable and suggest a fair score.

Data:
- Question Number: {question_number}
- Student Answer: {student_text[:500]}...
- Reference Answer: {reference_text[:500]}...
- Scored Marks: {scored_marks}
- Similarity Score: {similarity}
- OCR Confidence: {ocr_confidence}
- Max Marks: {max_marks}

Rules:
1. Do NOT change the marks; only suggest.
2. Flag suspicious cases.
3. Flag if similarity is low but student mentions core concepts.
4. Flag if similarity is high but answer is too short or incomplete.
5. Flag if OCR confidence is low.
6. Suggest a reasonable score out of {max_marks} based on the student's answer quality.
7. Output ONLY JSON in this format:

{{
  "verificationFlag": true/false,
  "reason": "<short_reason>",
  "gemini_marks": <int>
}}
"""

    try:
        logger.info(f"🤖 Calling Gemini for verification (Q{question_number})...")
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(prompt)
        text = response.text
        
        cleaned_text = text.strip().strip("`").strip("json").strip()
        result = json.loads(cleaned_text)
        result["gemini_marks"] = int(result.get("gemini_marks", 0))
        
        logger.info(f"✅ Gemini verification: Flag={result.get('verificationFlag')}, Suggested={result.get('gemini_marks')}")
        
        return result

    except Exception as e:
        logger.warning(f"⚠️  Gemini verification failed: {str(e)}")
        return {
            "verificationFlag": False,
            "reason": f"Gemini error: {str(e)}",
            "gemini_marks": 0
        }

def compare_and_score(exam_id: str, student_id: str) -> Dict[str, Any]:
    logger.info("\n" + "="*60)
    logger.info("⚖️  EVALUATION STARTED")
    logger.info("="*60)
    logger.info(f"🆔 Exam ID: {exam_id}")
    logger.info(f"👤 Student ID: {student_id}")
    
    exam_id = validate_id(exam_id, "exam_id")
    student_id = validate_id(student_id, "student_id")
    
    logger.info(f"📋 Exam ID validated: {exam_id}")
    logger.info(f"📋 Student ID validated: {student_id}")

    # 1) Load scheme
    logger.info("\n--- Step 1: Loading Marking Scheme ---")
    scheme_doc = col_schema.find_one({"examId": exam_id}, sort=[("_id", -1)])
    if not scheme_doc:
        logger.error("❌ No scheme found for given examId in schema_db.schema_extracted_answers")
        raise RuntimeError("No scheme found for given examId in schema_db.schema_extracted_answers")

    logger.info(f"✅ Scheme found: {scheme_doc.get('_id')}")
    
    structured = safe_json_loads(scheme_doc.get("structuredData", "{}"))
    scheme_questions = structured.get("questions", [])
    
    if not scheme_questions:
        logger.error("❌ Scheme has no parsed questions")
        raise RuntimeError("Scheme has no parsed questions")
    
    logger.info(f"📝 Scheme has {len(scheme_questions)} questions")

    # 2) Load student OCR answers
    logger.info("\n--- Step 2: Loading Student Answers ---")
    student_pages = list(col_student.find({"examId": exam_id, "studentId": student_id}))
    
    if not student_pages:
        logger.error("❌ No student answers found")
        raise RuntimeError("No student answers found for given examId + studentId in ai_evaluation_system")

    logger.info(f"✅ Found {len(student_pages)} pages of student answers")
    
    # Group by question number
    grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for p in student_pages:
        qn = p.get("questionNumber", -1)
        if isinstance(qn, int) and qn > 0:
            grouped[qn].append(p)
    
    logger.info(f"📊 Grouped into {len(grouped)} questions")
    for qn, pages in grouped.items():
        logger.info(f"   Q{qn}: {len(pages)} page(s)")

    # 3) Evaluate each question
    logger.info("\n--- Step 3: Evaluating Each Question ---")
    per_question_results = []
    total_scored = 0
    total_max = 0

    for idx, q in enumerate(scheme_questions):
        qn = q.get("questionNumber")
        max_marks = q.get("maxMarks", 0) or 0
        total_max += max_marks

        logger.info(f"\n🔍 Evaluating Question {qn} (Max: {max_marks} marks)")
        
        reference_text = build_reference_text(q)
        logger.info(f"   Reference text length: {len(reference_text)} characters")

        student_text = ""
        ocr_conf_avg = 0.0
        
        if qn in grouped:
            student_text = aggregate_student_answers(grouped[qn])
            confs = [float(p.get("confidence", 0)) for p in grouped[qn] if "confidence" in p]
            ocr_conf_avg = sum(confs) / len(confs) if confs else 0.0
            logger.info(f"   Student answer length: {len(student_text)} characters")
            logger.info(f"   Average OCR confidence: {ocr_conf_avg:.2f}")
        else:
            logger.warning(f"   ⚠️  No student answer found for Q{qn}")

        # Calculate similarity
        if not student_text.strip():
            similarity = 0.0
            scored_marks = 0
            logger.warning(f"   📉 No answer provided: 0 marks")
        else:
            [e_ref, e_student] = embed([reference_text, student_text])
            similarity = cosine(e_ref, e_student)
            scored_marks = int(round(max(0.0, min(1.0, similarity)) * max_marks))
            
            logger.info(f"   🎯 Similarity: {similarity:.4f}")
            logger.info(f"   ✅ Scored: {scored_marks}/{max_marks} marks")

        total_scored += scored_marks

        # Flags
        q_flags = flags_for(similarity, ocr_conf_avg)
        if q_flags:
            logger.warning(f"   🚩 Flags: {', '.join(q_flags)}")

        # Gemini verification
        verification = verify_with_gemini(qn, student_text, reference_text, scored_marks,
                                         similarity, ocr_conf_avg, max_marks)
        if verification.get("verificationFlag", False):
            q_flags.append("GEMINI_VERIFICATION_FLAG")
            q_flags.append(f"Reason: {verification.get('reason', '')}")
            logger.warning(f"   🤖 Gemini flagged: {verification.get('reason')}")

        per_question_results.append({
            "questionNumber": qn,
            "maxMarks": max_marks,
            "scoredMarks": scored_marks,
            "gemini_marks": verification.get("gemini_marks", 0),
            "similarity": round(similarity, 4),
            "ocrConfidenceAvg": round(ocr_conf_avg, 3),
            "flags": q_flags,
            "verification": verification,
        })

    # Overall results
    overall = {
        "totalMaxMarks": total_max,
        "totalScoredMarks": total_scored,
        "percentage": round((total_scored / total_max) * 100, 2) if total_max > 0 else 0.0
    }

    logger.info("\n" + "="*60)
    logger.info(f"📊 EVALUATION SUMMARY")
    logger.info("="*60)
    logger.info(f"   Total Score: {total_scored}/{total_max} ({overall['percentage']}%)")
    logger.info(f"   Questions Evaluated: {len(per_question_results)}")
    logger.info(f"   Flagged Questions: {sum(1 for q in per_question_results if q['flags'])}")
    logger.info("="*60)

    # Build result document
    result_doc = {
        "examId": exam_id,
        "studentId": student_id,
        "subjectId": scheme_doc.get("subjectId"),
        "professorId": scheme_doc.get("professorId"),
        "schemeRefId": scheme_doc["_id"],
        "generatedAt": datetime.utcnow(),
        "method": {
            "embeddingModel": EMBED_MODEL,
            "scoring": "round(similarity * maxMarks)",
            "similarity": "cosine",
            "flags": {
                "lowSimilarity": LOW_SIMILARITY_FLAG,
                "borderline": BORDERLINE_SIMILARITY,
                "high": HIGH_SIMILARITY
            }
        },
        "perQuestion": per_question_results,
        "overall": overall
    }

    # 4) Store in result_db
    logger.info("\n--- Step 4: Saving Results ---")
    # Use replace_one with upsert to update existing or insert new
    result = col_results.replace_one(
        {'examId': exam_id, 'studentId': student_id},
        result_doc,
        upsert=True
    )
    
    if result.upserted_id:
        logger.info(f"✅ Inserted new evaluation with ID: {result.upserted_id}")
        result_doc["_id"] = result.upserted_id
    else:
        logger.info(f"✅ Updated existing evaluation for {student_id}")
    
    return result_doc

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare student answers with scheme and score.")
    parser.add_argument("--exam-id", required=True, help="Exam ID (any string format)")
    parser.add_argument("--student-id", required=True, help="Student ID (any string format)")
    args = parser.parse_args()

    try:
        out = compare_and_score(args.exam_id, args.student_id)
        logger.info("\n✅ SUCCESS: Evaluation completed")
        logger.info(f"   Score: {out['overall']['totalScoredMarks']}/{out['overall']['totalMaxMarks']}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)