from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import easyocr
from pdf2image import convert_from_path
import os
import numpy as np
from PIL import Image
import google.generativeai as genai
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict
import logging
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Certificate Metadata Extraction API",
    description="Extract metadata from certificate images and PDFs using OCR and Gemini AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Initialize EasyOCR reader (load once at startup)
reader = easyocr.Reader(['en'], gpu=False)

PROMPT_TEMPLATE = """
Extract the following fields from the text. Output ONLY in this exact format, one per line:
Student Name - [name or 'not found']
University Name - [name or 'not found']
Degree Name - [degree or 'not found']
Specialization - [spec or 'not found']
Grade - [grade or 'not found']
Certificate Id - [id or 'not found']
Registration Number - [reg or 'not found']
Date of Issue - [date or 'not found']

Examples:
Text: John Doe graduated from Harvard University with a Master of Arts in History, Grade: A, Cert ID: CERT123, Reg No: REG456, Issued: 2023-05-15.
Output:
Student Name - John Doe
University Name - Harvard University
Degree Name - Master of Arts
Specialization - History
Grade - A
Certificate Id/Sl. No. - CERT123
Registration Number/Reg No. /No. - REG456
Date of Issue - 2023-05-15

Text: Alice Smith, MIT, BS in Physics, GPA 3.8, ID: PHYS-789, Reg: MIT-101, Date/Graduated Year: 2024-01-10.
Output:
Student Name - Alice Smith
University Name - MIT
Degree Name - BS
Specialization - Physics
Grade - GPA 3.8
Certificate Id/Sl. No. - PHYS-789
Registration Number/Reg No./ No. - MIT-101
Date of Issue - 2024-01-10

Text: {text}
"""


def extract_text_from_image(image_path: str) -> str:
    """Extract text from an image file using EasyOCR"""
    try:
        results = reader.readtext(image_path)
        text = ' '.join([result[1] for result in results])
        return text
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        raise


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file using OCR"""
    try:
        images = convert_from_path(pdf_path)
        full_text = []
        
        for i, image in enumerate(images):
            logger.info(f"Processing page {i+1}/{len(images)}")
            image_np = np.array(image)
            results = reader.readtext(image_np)
            page_text = ' '.join([result[1] for result in results])
            full_text.append(page_text)
        
        return '\n\n'.join(full_text)
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise


def save_to_json_file(data: Dict, filename: str) -> str:
    """Save metadata to a JSON file"""
    output_filename = f"metadata_{filename.replace('.', '_')}.json"
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Metadata saved to {output_filename}")
        return output_filename
    except Exception as e:
        logger.error(f"Error saving JSON file: {str(e)}")
        raise

def extract_metadata_with_gemini(text: str) -> Dict[str, str]:
    """Extract structured metadata using Gemini AI"""
    try:
        prompt = PROMPT_TEMPLATE.format(text=text)
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        logger.info(f"Gemini raw response: {result}")
        
        # Parse the result into JSON
        lines = result.strip().split('\n')
        data = {}
        
        # Define standard field names for consistency
        field_mapping = {
            'student name': 'Student Name',
            'university name': 'University Name',
            'degree name': 'Degree Name',
            'specialization': 'Specialization',
            'grade': 'Grade',
            'certificate id': 'Certificate Id',
            'registration number': 'Registration Number',
            'date of issue': 'Date of Issue'
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try multiple separators
            separator = None
            if ' - ' in line:
                separator = ' - '
            elif ': ' in line:
                separator = ': '
            elif '- ' in line:
                separator = '- '
            
            if separator:
                parts = line.split(separator, 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    
                    # Normalize the key
                    key_lower = key.lower()
                    for search_key, standard_key in field_mapping.items():
                        if search_key in key_lower:
                            key = standard_key
                            break
                    
                    data[key] = value
        
        # Ensure all expected fields are present
        for standard_key in field_mapping.values():
            if standard_key not in data:
                data[standard_key] = 'not found'
        
        return data
    except Exception as e:
        logger.error(f"Error extracting metadata with Gemini: {str(e)}")
        raise


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return JSONResponse(
        content={
            "message": "Certificate Metadata Extraction API",
            "version": "1.0.0",
            "endpoints": {
                "/extract": "POST - Extract metadata from certificate image or PDF",
                "/health": "GET - Health check endpoint"
            }
        },
        media_type="application/json"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "ocr_loaded": reader is not None,
            "gemini_configured": GEMINI_API_KEY is not None
        },
        media_type="application/json"
    )


@app.post("/extract")
async def extract_certificate_metadata(file: UploadFile = File(...)):
    """
    Extract metadata from certificate image or PDF
    
    Parameters:
    - file: Certificate image (JPG, PNG, TIFF, BMP) or PDF file
    
    Returns:
    - JSON object with extracted metadata
    """
    temp_file_path = None
    
    try:
        # Validate file
        validate_file(file)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)
        
        logger.info(f"Processing file: {file.filename}")
        
        # Extract text based on file type
        file_ext = Path(file.filename).suffix.lower()
        if file_ext == '.pdf':
            extracted_text = extract_text_from_pdf(temp_file_path)
        else:
            extracted_text = extract_text_from_image(temp_file_path)
        
        logger.info(f"Extracted text length: {len(extracted_text)} characters")
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the file. Please ensure the image is clear and readable."
            )
        
        # Extract metadata using Gemini
        metadata = extract_metadata_with_gemini(extracted_text)
        
        # Save metadata to JSON file
        json_filename = save_to_json_file(metadata, file.filename)
        
        # Prepare JSON response
        response_data = {
            "status": "success",
            "filename": file.filename,
            "extracted_text_length": len(extracted_text),
            "metadata": metadata,
            "json_file": json_filename
        }
        # Return JSON response with proper content type
        return JSONResponse(
            content=response_data,
            media_type="application/json"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Error deleting temporary file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)