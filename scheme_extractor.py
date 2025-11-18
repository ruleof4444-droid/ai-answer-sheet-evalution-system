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

os.environ["OPENAI_API_KEY"] = "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"

load_dotenv()

client = OpenAI()

# MongoDB setup (schema_db)
mongo_uri = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
schema_db = MongoClient(mongo_uri)["schema_db"]
schema_collection = schema_db["schema_extracted_answers"]

# Prompt to structure scheme PDF text
SCHEME_EXTRACTION_PROMPT = """
You are an expert examiner and academic text analyzer.
You will extract evaluation scheme information from a PDF page.
Follow these rules carefully:

1. Extract every question number and the question text exactly as provided.
2. Extract maximum marks allotted to each question (like "10 marks", "5M").
3. For each question, break down the model answer into multiple conceptual points.
4. Each conceptual point must include:
   - A clear description of the concept
   - Important keywords from that concept
   - Marks allotted to that concept
   - Whether it is a mandatory concept (true/false)
   - Acceptable variations or synonyms students may use

5. For each question, provide:
   - Full marks requirements (describe when full marks are awarded)
   - Partial marks conditions
   - Common mistakes to look for
   - Must-include points
   - Reference answer (if available)
   - Hints (optional)
   - Difficulty (easy, medium, hard)

6. Return output strictly in valid JSON format with this structure:

{
  "questions": [
    {
      "questionNumber": <number>,
      "questionText": "<text>",
      "maxMarks": <number>,
      "concepts": [
        {
          "conceptId": "Q<questionNumber>_C<index>",
          "description": "<text>",
          "keywords": ["word1", "word2"],
          "marks": <number>,
          "isMandatory": <true/false>,
          "acceptableVariations": ["variation1", "variation2"]
        }
      ],
      "evaluationCriteria": {
        "fullMarksRequirements": "<text>",
        "partialMarksConditions": "<text>",
        "commonMistakes": ["mistake1", "mistake2"],
        "mustIncludePoints": ["point1", "point2"]
      },
      "referenceAnswer": "<text>",
      "onlyAnswer": "<text>",
      "hints": ["hint1", "hint2"],
      "difficulty": "<easy|medium|hard>"
    }
  ],
  "metadata": {
    "totalMarks": <sum_of_marks>,
    "numberOfQuestions": <count>
  }
}
"""

def extract_scheme_text(pdf_path):
    doc = fitz.open(pdf_path)
    raw_text = ""

    for page in doc:
        text = page.get_text("text").strip()
        if not text:
            # If text not directly extractable, fallback to OCR
            pix = page.get_pixmap(dpi=200)
            image_bytes = pix.tobytes()
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract text from this exam scheme PDF page."},
                    {"role": "user",
                     "content": [
                         {"type": "text", "text": "Extract all text visible on this page without formatting changes."},
                         {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                     ]}
                ]
            )

            text = response.choices[0].message.content

        raw_text += text + "\n\n"

    return raw_text

def parse_and_store_scheme(pdf_path, examId=None, professorId=None, subjectId=None):
    # Set default string IDs if not provided
    if not examId:
        import uuid
        examId = str(uuid.uuid4())
    if not professorId:
        import uuid
        professorId = str(uuid.uuid4())
    if not subjectId:
        import uuid
        subjectId = str(uuid.uuid4())
    
    # Normalize to strings
    examId = str(examId).strip()
    professorId = str(professorId).strip()
    subjectId = str(subjectId).strip()

    print("\n--- Extracting raw text from scheme PDF ---")

    raw_text = extract_scheme_text(pdf_path)

    print("\n--- Calling GPT to structure schema ---")

    structured_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Convert extracted scheme text into structured JSON."},
            {"role": "user", "content": raw_text},
            {"role": "user", "content": SCHEME_EXTRACTION_PROMPT}
        ]
    )

    structured_json = structured_response.choices[0].message.content

    # Insert into schema_db
    record = {
        "examId": examId,
        "professorId": professorId,
        "subjectId": subjectId,
        "pdfMetadata": {
            "fileName": os.path.basename(pdf_path),
            "filePath": os.path.abspath(pdf_path),
            "fileSize": os.path.getsize(pdf_path),
            "totalPages": fitz.open(pdf_path).page_count,
            "uploadedAt": datetime.utcnow(),
            "extractionMethod": "text_extraction"
        },
        "rawExtractedText": raw_text,
        "structuredData": structured_json,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }

    result = schema_collection.insert_one(record)
    print(f"[SUCCESS] Schema stored with ID: {result.inserted_id}")

    return structured_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and structure evaluation scheme from PDF.")
    parser.add_argument("pdf_path", help="Path to the scheme PDF file")
    parser.add_argument("--exam-id", help="Exam ID (any string format, auto-generated if not provided)")
    parser.add_argument("--professor-id", help="Professor ID (any string format, auto-generated if not provided)")
    parser.add_argument("--subject-id", help="Subject ID (any string format, auto-generated if not provided)")

    args = parser.parse_args()

    # Convert to absolute path to handle paths from anywhere on the PC
    pdf_path = os.path.abspath(args.pdf_path)
    parse_and_store_scheme(pdf_path, args.exam_id, args.professor_id, args.subject_id)
