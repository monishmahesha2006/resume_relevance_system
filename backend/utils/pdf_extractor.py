"""
PDF Text Extraction Utilities
Supports PyMuPDF and pdfplumber for robust PDF text extraction
"""

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

import pdfplumber
import docx2txt
import os
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF and DOCX files using multiple libraries for robustness"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.doc']
    
    def extract_text_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF (faster, good for most PDFs)"""
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available, skipping")
            return ""
        
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed for {file_path}: {e}")
            return ""
    
    def extract_text_pdfplumber(self, file_path: str) -> str:
        """Extract text using pdfplumber (better for complex layouts)"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"pdfplumber extraction failed for {file_path}: {e}")
            return ""
    
    def extract_text_docx(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            logger.error(f"DOCX extraction failed for {file_path}: {e}")
            return ""
    
    def extract_text(self, file_path: str) -> str:
        """Main extraction method with fallback strategies"""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            # Try PyMuPDF first if available, fallback to pdfplumber
            if PYMUPDF_AVAILABLE:
                text = self.extract_text_pymupdf(file_path)
                if not text.strip():
                    logger.info(f"PyMuPDF failed, trying pdfplumber for {file_path}")
                    text = self.extract_text_pdfplumber(file_path)
            else:
                logger.info(f"PyMuPDF not available, using pdfplumber for {file_path}")
                text = self.extract_text_pdfplumber(file_path)
            return text
        
        elif file_ext in ['.docx', '.doc']:
            return self.extract_text_docx(file_path)
        
        else:
            logger.error(f"Unsupported file format: {file_ext}")
            return ""
    
    def extract_text_with_metadata(self, file_path: str) -> Dict[str, str]:
        """Extract text along with file metadata"""
        text = self.extract_text(file_path)
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        return {
            'file_path': file_path,
            'file_name': file_name,
            'file_size': file_size,
            'text': text,
            'word_count': len(text.split()) if text else 0
        }
    
    def batch_extract(self, directory_path: str, file_pattern: str = "*") -> List[Dict[str, str]]:
        """Extract text from all files in a directory"""
        extracted_files = []
        
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return extracted_files
        
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in self.supported_formats:
                    logger.info(f"Extracting text from: {filename}")
                    extracted_data = self.extract_text_with_metadata(file_path)
                    if extracted_data['text'].strip():  # Only add if text was extracted
                        extracted_files.append(extracted_data)
                    else:
                        logger.warning(f"No text extracted from: {filename}")
        
        logger.info(f"Successfully extracted text from {len(extracted_files)} files")
        return extracted_files


def main():
    """Test the PDF extractor with sample files"""
    extractor = PDFExtractor()
    
    # Test with sample files
    jd_dir = "data/JD"
    resume_dir = "data/Resumes"
    
    print("Extracting Job Descriptions...")
    jd_files = extractor.batch_extract(jd_dir)
    for jd in jd_files:
        print(f"JD: {jd['file_name']} - {jd['word_count']} words")
    
    print("\nExtracting Resumes...")
    resume_files = extractor.batch_extract(resume_dir)
    for resume in resume_files:
        print(f"Resume: {resume['file_name']} - {resume['word_count']} words")


if __name__ == "__main__":
    main()
