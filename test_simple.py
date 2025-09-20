"""
Simple test script to verify the system works with basic functionality
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pdf_extraction():
    """Test PDF extraction with pdfplumber only"""
    try:
        from utils.pdf_extractor import PDFExtractor
        
        extractor = PDFExtractor()
        
        # Test with sample files
        jd_dir = "data/JD"
        resume_dir = "data/Resumes"
        
        print("Testing PDF extraction...")
        
        if os.path.exists(jd_dir):
            jd_files = extractor.batch_extract(jd_dir)
            print(f"Extracted {len(jd_files)} job descriptions")
            for jd in jd_files:
                print(f"  - {jd['file_name']}: {jd['word_count']} words")
        
        if os.path.exists(resume_dir):
            resume_files = extractor.batch_extract(resume_dir)
            print(f"Extracted {len(resume_files)} resumes")
            for resume in resume_files:
                print(f"  - {resume['file_name']}: {resume['word_count']} words")
        
        return True
    except Exception as e:
        print(f"PDF extraction test failed: {e}")
        return False

def test_text_preprocessing():
    """Test text preprocessing"""
    try:
        from utils.text_preprocessor_simple import SimpleTextPreprocessor
        
        preprocessor = SimpleTextPreprocessor()
        
        # Sample text
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
        
        print("Testing text preprocessing...")
        result = preprocessor.preprocess_resume(sample_text)
        
        print(f"  - Word count: {result['word_count']}")
        print(f"  - Skills found: {len(result['skills'])}")
        print(f"  - Education found: {len(result['education'])}")
        print(f"  - Experience years: {result['experience_years']}")
        
        return True
    except Exception as e:
        print(f"Text preprocessing test failed: {e}")
        return False

def test_database():
    """Test database operations"""
    try:
        from utils.database_manager import DatabaseManager
        
        print("Testing database operations...")
        db_manager = DatabaseManager()
        
        # Test statistics
        stats = db_manager.get_statistics()
        print(f"  - Database stats: {stats}")
        
        return True
    except Exception as e:
        print(f"Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Simple System Tests")
    print("=" * 50)
    
    tests = [
        ("PDF Extraction", test_pdf_extraction),
        ("Text Preprocessing", test_text_preprocessing),
        ("Database Operations", test_database)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
