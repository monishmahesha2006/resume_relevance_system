"""
Text Preprocessing Utilities
Clean and normalize extracted text, split into sections
"""

import re
import spacy
import nltk
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')


class TextPreprocessor:
    """Clean and preprocess extracted text from resumes and job descriptions"""
    
    def __init__(self):
        # Load spaCy model (download if not available)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Common section headers for resumes
        self.resume_sections = {
            'contact': ['contact', 'personal information', 'personal details'],
            'summary': ['summary', 'profile', 'objective', 'about'],
            'experience': ['experience', 'work experience', 'employment', 'professional experience'],
            'education': ['education', 'academic', 'qualifications', 'degrees'],
            'skills': ['skills', 'technical skills', 'core competencies', 'expertise'],
            'projects': ['projects', 'project experience', 'portfolio'],
            'certifications': ['certifications', 'certificates', 'licenses'],
            'achievements': ['achievements', 'awards', 'honors', 'recognition']
        }
        
        # Common JD sections
        self.jd_sections = {
            'title': ['job title', 'position', 'role'],
            'company': ['company', 'organization', 'employer'],
            'location': ['location', 'place', 'city', 'state'],
            'requirements': ['requirements', 'qualifications', 'must have', 'required'],
            'responsibilities': ['responsibilities', 'duties', 'role', 'key responsibilities'],
            'skills': ['skills', 'technical skills', 'competencies'],
            'experience': ['experience', 'years of experience', 'work experience'],
            'education': ['education', 'degree', 'qualification']
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove special characters but keep alphanumeric, spaces, and common punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def extract_sections(self, text: str, doc_type: str = 'resume') -> Dict[str, str]:
        """Extract sections from resume or job description"""
        sections = {}
        text_lower = text.lower()
        
        # Choose section patterns based on document type
        section_patterns = self.resume_sections if doc_type == 'resume' else self.jd_sections
        
        for section_name, keywords in section_patterns.items():
            section_text = self._extract_section_by_keywords(text, keywords)
            if section_text:
                sections[section_name] = section_text
        
        return sections
    
    def _extract_section_by_keywords(self, text: str, keywords: List[str]) -> str:
        """Extract section based on keyword matching"""
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this line is a section header
            if any(keyword in line_lower for keyword in keywords):
                in_section = True
                continue
            
            # If we're in a section and line is not empty
            if in_section and line.strip():
                # Check if this is a new section (common headers)
                if self._is_section_header(line_lower):
                    break
                section_lines.append(line.strip())
        
        return ' '.join(section_lines)
    
    def _is_section_header(self, line: str) -> bool:
        """Check if a line is likely a section header"""
        # Common section header patterns
        header_patterns = [
            r'^(experience|education|skills|projects|certifications|achievements)',
            r'^(work|professional|academic|technical)',
            r'^(summary|profile|objective|about)',
            r'^(contact|personal)',
            r'^\d{4}\s*[-–]\s*\d{4}',  # Date ranges
            r'^[A-Z][A-Z\s]+$'  # All caps lines
        ]
        
        for pattern in header_patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using NLP"""
        skills = []
        
        if self.nlp:
            doc = self.nlp(text)
            
            # Extract noun phrases that might be skills
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3:  # Skills are usually 1-3 words
                    skills.append(chunk.text.lower())
            
            # Extract named entities (organizations, technologies)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'TECHNOLOGY']:
                    skills.append(ent.text.lower())
        
        # Also extract from common skill patterns
        skill_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Two word technologies
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\w+\s+(programming|language|framework|tool|software)\b'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.extend([match.lower() for match in matches])
        
        return list(set(skills))  # Remove duplicates
    
    def extract_education(self, text: str) -> List[str]:
        """Extract education information"""
        education = []
        
        # Common degree patterns
        degree_patterns = [
            r'\b(B\.S\.|B\.A\.|M\.S\.|M\.A\.|PhD|Bachelor|Master|Doctorate)\b',
            r'\b(Computer Science|Engineering|Business|Management)\b',
            r'\b(University|College|Institute)\b'
        ]
        
        for pattern in degree_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            education.extend(matches)
        
        return list(set(education))
    
    def extract_experience_years(self, text: str) -> Optional[int]:
        """Extract years of experience"""
        # Look for patterns like "5 years", "3+ years", etc.
        patterns = [
            r'(\d+)\+?\s*years?\s*(of\s*)?experience',
            r'(\d+)\+?\s*years?\s*(of\s*)?work',
            r'(\d+)\+?\s*years?\s*(of\s*)?professional'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def preprocess_resume(self, text: str) -> Dict[str, any]:
        """Complete preprocessing for resume"""
        cleaned_text = self.clean_text(text)
        sections = self.extract_sections(cleaned_text, 'resume')
        skills = self.extract_skills(cleaned_text)
        education = self.extract_education(cleaned_text)
        experience_years = self.extract_experience_years(cleaned_text)
        
        return {
            'cleaned_text': cleaned_text,
            'sections': sections,
            'skills': skills,
            'education': education,
            'experience_years': experience_years,
            'word_count': len(cleaned_text.split())
        }
    
    def preprocess_jd(self, text: str) -> Dict[str, any]:
        """Complete preprocessing for job description"""
        cleaned_text = self.clean_text(text)
        sections = self.extract_sections(cleaned_text, 'jd')
        skills = self.extract_skills(cleaned_text)
        education = self.extract_education(cleaned_text)
        experience_years = self.extract_experience_years(cleaned_text)
        
        return {
            'cleaned_text': cleaned_text,
            'sections': sections,
            'skills': skills,
            'education': education,
            'experience_years': experience_years,
            'word_count': len(cleaned_text.split())
        }


def main():
    """Test the text preprocessor"""
    preprocessor = TextPreprocessor()
    
    # Sample text for testing
    sample_text = """
    John Doe
    Software Engineer
    
    Experience:
    - 5 years of experience in Python development
    - Worked with Django, Flask frameworks
    - Experience with AWS, Docker
    
    Education:
    - B.S. Computer Science from MIT
    - M.S. Software Engineering from Stanford
    
    Skills:
    - Python, JavaScript, React
    - Machine Learning, Data Science
    - SQL, MongoDB, PostgreSQL
    """
    
    result = preprocessor.preprocess_resume(sample_text)
    print("Preprocessed Resume:")
    print(f"Skills: {result['skills']}")
    print(f"Education: {result['education']}")
    print(f"Experience Years: {result['experience_years']}")


if __name__ == "__main__":
    main()
