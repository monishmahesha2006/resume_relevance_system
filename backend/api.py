"""
FastAPI Backend for Resume Relevance System
Provides REST API endpoints for the system
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import tempfile
from typing import List, Optional, Dict
import logging
from datetime import datetime

# Import our modules
from utils.pdf_extractor import PDFExtractor
from utils.text_preprocessor import TextPreprocessor
from models.feature_engineering import FeatureEngineer
from models.relevance_scorer import RelevanceScorer
from utils.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Relevance System API",
    description="API for automated resume-JD relevance checking",
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

# Initialize components
pdf_extractor = PDFExtractor()
text_preprocessor = TextPreprocessor()
feature_engineer = FeatureEngineer()
relevance_scorer = RelevanceScorer()
db_manager = DatabaseManager()

# Create upload directories
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Resume Relevance System API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/upload/job-description")
async def upload_job_description(file: UploadFile = File(...)):
    """Upload and process a job description"""
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, f"jd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text
        extracted_data = pdf_extractor.extract_text_with_metadata(file_path)
        if not extracted_data['text'].strip():
            raise HTTPException(status_code=400, detail="No text extracted from the file")
        
        # Preprocess text
        processed_data = text_preprocessor.preprocess_jd(extracted_data['text'])
        
        # Save to database
        jd_id = db_manager.save_job_description(
            file.filename,
            file_path,
            extracted_data['text'],
            processed_data
        )
        
        return {
            "message": "Job description uploaded successfully",
            "jd_id": jd_id,
            "file_name": file.filename,
            "word_count": processed_data['word_count'],
            "extracted_sections": list(processed_data['sections'].keys())
        }
    
    except Exception as e:
        logger.error(f"Error uploading job description: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and process a resume"""
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text
        extracted_data = pdf_extractor.extract_text_with_metadata(file_path)
        if not extracted_data['text'].strip():
            raise HTTPException(status_code=400, detail="No text extracted from the file")
        
        # Preprocess text
        processed_data = text_preprocessor.preprocess_resume(extracted_data['text'])
        
        # Save to database
        resume_id = db_manager.save_resume(
            file.filename,
            file_path,
            extracted_data['text'],
            processed_data
        )
        
        return {
            "message": "Resume uploaded successfully",
            "resume_id": resume_id,
            "file_name": file.filename,
            "word_count": processed_data['word_count'],
            "extracted_sections": list(processed_data['sections'].keys())
        }
    
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match/{resume_id}/{jd_id}")
async def match_resume_jd(resume_id: int, jd_id: int):
    """Match a specific resume with a job description"""
    try:
        # Get resume and JD data from database
        resumes = db_manager.get_resumes()
        jds = db_manager.get_job_descriptions()
        
        resume_data = next((r for r in resumes if r['id'] == resume_id), None)
        jd_data = next((j for j in jds if j['id'] == jd_id), None)
        
        if not resume_data:
            raise HTTPException(status_code=404, detail="Resume not found")
        if not jd_data:
            raise HTTPException(status_code=404, detail="Job description not found")
        
        # Parse processed data
        resume_processed = json.loads(resume_data['processed_data'])
        jd_processed = json.loads(jd_data['processed_data'])
        
        # Calculate feature scores
        feature_scores = feature_engineer.calculate_final_score(resume_processed, jd_processed)
        
        # Generate comprehensive analysis
        analysis_result = relevance_scorer.generate_comprehensive_analysis(
            resume_processed, jd_processed, feature_scores
        )
        
        # Save result to database
        result_id = db_manager.save_matching_result(resume_id, jd_id, analysis_result)
        
        return {
            "message": "Matching completed successfully",
            "result_id": result_id,
            "resume_name": resume_data['file_name'],
            "jd_name": jd_data['file_name'],
            "analysis": analysis_result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching resume and JD: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match/all")
async def match_all_resumes_jds():
    """Match all resumes with all job descriptions"""
    try:
        resumes = db_manager.get_resumes()
        jds = db_manager.get_job_descriptions()
        
        if not resumes:
            raise HTTPException(status_code=400, detail="No resumes found")
        if not jds:
            raise HTTPException(status_code=400, detail="No job descriptions found")
        
        results = []
        total_matches = len(resumes) * len(jds)
        completed_matches = 0
        
        for resume in resumes:
            for jd in jds:
                try:
                    # Parse processed data
                    resume_processed = json.loads(resume['processed_data'])
                    jd_processed = json.loads(jd['processed_data'])
                    
                    # Calculate feature scores
                    feature_scores = feature_engineer.calculate_final_score(resume_processed, jd_processed)
                    
                    # Generate comprehensive analysis
                    analysis_result = relevance_scorer.generate_comprehensive_analysis(
                        resume_processed, jd_processed, feature_scores
                    )
                    
                    # Save result to database
                    result_id = db_manager.save_matching_result(resume['id'], jd['id'], analysis_result)
                    
                    results.append({
                        "resume_name": resume['file_name'],
                        "jd_name": jd['file_name'],
                        "relevance_score": analysis_result['relevance_score'],
                        "verdict": analysis_result['verdict']
                    })
                    
                    completed_matches += 1
                    logger.info(f"Completed {completed_matches}/{total_matches} matches")
                
                except Exception as e:
                    logger.error(f"Error matching {resume['file_name']} with {jd['file_name']}: {e}")
                    continue
        
        return {
            "message": f"Bulk matching completed",
            "total_matches": completed_matches,
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job-descriptions")
async def get_job_descriptions():
    """Get all job descriptions"""
    try:
        jds = db_manager.get_job_descriptions()
        return {"job_descriptions": jds}
    except Exception as e:
        logger.error(f"Error getting job descriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/resumes")
async def get_resumes():
    """Get all resumes"""
    try:
        resumes = db_manager.get_resumes()
        return {"resumes": resumes}
    except Exception as e:
        logger.error(f"Error getting resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/matching-results")
async def get_matching_results(
    limit: Optional[int] = Query(None, description="Limit number of results"),
    verdict: Optional[str] = Query(None, description="Filter by verdict (High/Medium/Low)")
):
    """Get matching results with optional filtering"""
    try:
        if verdict:
            results = db_manager.get_matches_by_verdict(verdict)
        else:
            results = db_manager.get_matching_results(limit)
        
        return {"matching_results": results}
    except Exception as e:
        logger.error(f"Error getting matching results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/matching-summary")
async def get_matching_summary():
    """Get matching summary"""
    try:
        summary = db_manager.get_matching_summary()
        return {"matching_summary": summary}
    except Exception as e:
        logger.error(f"Error getting matching summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/top-matches")
async def get_top_matches(limit: int = Query(10, description="Number of top matches to return")):
    """Get top matches"""
    try:
        top_matches = db_manager.get_top_matches(limit)
        return {"top_matches": top_matches}
    except Exception as e:
        logger.error(f"Error getting top matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search_matches(query: str = Query(..., description="Search query")):
    """Search matches by resume or JD name"""
    try:
        results = db_manager.search_matches(query)
        return {"search_results": results}
    except Exception as e:
        logger.error(f"Error searching matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics")
async def get_statistics():
    """Get database statistics"""
    try:
        stats = db_manager.get_statistics()
        return {"statistics": stats}
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/job-description/{jd_id}")
async def delete_job_description(jd_id: int):
    """Delete a job description"""
    try:
        success = db_manager.delete_job_description(jd_id)
        if success:
            return {"message": "Job description deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete job description")
    except Exception as e:
        logger.error(f"Error deleting job description: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/resume/{resume_id}")
async def delete_resume(resume_id: int):
    """Delete a resume"""
    try:
        success = db_manager.delete_resume(resume_id)
        if success:
            return {"message": "Resume deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete resume")
    except Exception as e:
        logger.error(f"Error deleting resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
