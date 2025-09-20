"""
Simplified Main Pipeline Script for Resume Relevance System
Processes existing datasets and runs the complete pipeline without heavy dependencies
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.utils.pdf_extractor import PDFExtractor
from backend.utils.text_preprocessor_simple import SimpleTextPreprocessor
from backend.utils.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleResumeRelevancePipeline:
    """Simplified pipeline for processing resumes and job descriptions"""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.text_preprocessor = SimpleTextPreprocessor()
        self.db_manager = DatabaseManager()
        
        # Data paths
        self.jd_dir = "data/JD"
        self.resume_dir = "data/Resumes"
        
        logger.info("Simple pipeline initialized successfully")
    
    def extract_and_process_files(self):
        """Extract text from all files and process them"""
        logger.info("Starting file extraction and processing...")
        
        # Process job descriptions
        logger.info("Processing job descriptions...")
        jd_files = self.pdf_extractor.batch_extract(self.jd_dir)
        jd_processed = []
        
        for jd_file in jd_files:
            logger.info(f"Processing JD: {jd_file['file_name']}")
            processed_data = self.text_preprocessor.preprocess_jd(jd_file['text'])
            
            # Save to database
            jd_id = self.db_manager.save_job_description(
                jd_file['file_name'],
                jd_file['file_path'],
                jd_file['text'],
                processed_data
            )
            
            jd_processed.append({
                'id': jd_id,
                'file_name': jd_file['file_name'],
                'processed_data': processed_data
            })
        
        # Process resumes
        logger.info("Processing resumes...")
        resume_files = self.pdf_extractor.batch_extract(self.resume_dir)
        resume_processed = []
        
        for resume_file in resume_files:
            logger.info(f"Processing Resume: {resume_file['file_name']}")
            processed_data = self.text_preprocessor.preprocess_resume(resume_file['text'])
            
            # Save to database
            resume_id = self.db_manager.save_resume(
                resume_file['file_name'],
                resume_file['file_path'],
                resume_file['text'],
                processed_data
            )
            
            resume_processed.append({
                'id': resume_id,
                'file_name': resume_file['file_name'],
                'processed_data': processed_data
            })
        
        logger.info(f"Processed {len(jd_processed)} job descriptions and {len(resume_processed)} resumes")
        return jd_processed, resume_processed
    
    def simple_matching(self, resume_data, jd_data):
        """Simple matching algorithm based on skills and keywords"""
        # Extract skills from both
        resume_skills = set(resume_data.get('skills', []))
        jd_skills = set(jd_data.get('skills', []))
        
        # Calculate skill overlap
        if not jd_skills:
            skill_score = 0.0
        else:
            skill_overlap = len(resume_skills.intersection(jd_skills))
            skill_score = skill_overlap / len(jd_skills)
        
        # Calculate education match
        resume_education = set(resume_data.get('education', []))
        jd_education = set(jd_data.get('education', []))
        
        if not jd_education:
            education_score = 0.0
        else:
            education_overlap = len(resume_education.intersection(jd_education))
            education_score = education_overlap / len(jd_education)
        
        # Calculate experience match
        resume_years = resume_data.get('experience_years', 0) or 0
        jd_years = jd_data.get('experience_years', 0) or 0
        
        if jd_years == 0:
            experience_score = 0.5  # Neutral if no requirement specified
        elif resume_years >= jd_years:
            experience_score = 1.0
        else:
            experience_score = resume_years / jd_years
        
        # Calculate keyword overlap in text
        resume_text = resume_data.get('cleaned_text', '').lower()
        jd_text = jd_data.get('cleaned_text', '').lower()
        
        # Simple keyword matching
        resume_words = set(resume_text.split())
        jd_words = set(jd_text.split())
        
        if not jd_words:
            keyword_score = 0.0
        else:
            keyword_overlap = len(resume_words.intersection(jd_words))
            keyword_score = keyword_overlap / len(jd_words)
        
        # Weighted final score
        final_score = (
            0.4 * skill_score +
            0.2 * education_score +
            0.2 * experience_score +
            0.2 * keyword_score
        )
        
        # Determine verdict
        if final_score >= 0.7:
            verdict = 'High'
        elif final_score >= 0.4:
            verdict = 'Medium'
        else:
            verdict = 'Low'
        
        # Calculate missing skills
        missing_skills = list(jd_skills - resume_skills)
        
        # Calculate missing education
        missing_education = list(jd_education - resume_education)
        
        # Experience analysis
        if jd_years > 0:
            if resume_years >= jd_years:
                exp_message = f"Meets experience requirement ({resume_years} years)"
            else:
                gap = jd_years - resume_years
                exp_message = f"Missing {gap} years of experience"
        else:
            exp_message = "No specific experience requirement"
        
        # Generate simple feedback
        feedback_parts = []
        
        if missing_skills:
            feedback_parts.append(f"Consider adding these skills: {', '.join(missing_skills[:3])}")
        
        if missing_education:
            feedback_parts.append(f"Consider highlighting relevant education: {', '.join(missing_education)}")
        
        if not missing_skills and not missing_education:
            feedback_parts.append("Good match! Skills and education align well with requirements.")
        
        feedback = ". ".join(feedback_parts) + "." if feedback_parts else "No specific feedback available."
        
        return {
            'relevance_score': round(final_score, 3),  # Store as decimal 0-1 for database
            'verdict': verdict,
            'hard_match_score': round(skill_score, 3),
            'soft_match_score': round(keyword_score, 3),
            'missing_skills': missing_skills,
            'missing_education': missing_education,
            'experience_analysis': {
                'gap': max(0, jd_years - resume_years),
                'meets_requirement': resume_years >= jd_years,
                'message': exp_message
            },
            'feedback': feedback,
            'strengths': [f"Strong technical skills: {', '.join(list(resume_skills)[:3])}"] if resume_skills else [],
            'improvement_areas': [f"Develop missing skills: {', '.join(missing_skills[:3])}"] if missing_skills else []
        }
    
    def run_matching(self, jd_processed, resume_processed):
        """Run matching between all resumes and job descriptions"""
        logger.info("Starting matching process...")
        
        total_matches = len(jd_processed) * len(resume_processed)
        completed_matches = 0
        results = []
        
        for resume in resume_processed:
            for jd in jd_processed:
                logger.info(f"Matching {resume['file_name']} with {jd['file_name']}")
                
                try:
                    # Calculate matching scores
                    analysis_result = self.simple_matching(
                        resume['processed_data'], 
                        jd['processed_data']
                    )
                    
                    # Save to database
                    result_id = self.db_manager.save_matching_result(
                        resume['id'], 
                        jd['id'], 
                        analysis_result
                    )
                    
                    results.append({
                        'resume_name': resume['file_name'],
                        'jd_name': jd['file_name'],
                        'relevance_score': round(analysis_result['relevance_score'] * 100, 1),  # Convert to percentage for display
                        'verdict': analysis_result['verdict'],
                        'result_id': result_id
                    })
                    
                    completed_matches += 1
                    logger.info(f"Completed {completed_matches}/{total_matches} matches")
                
                except Exception as e:
                    logger.error(f"Error matching {resume['file_name']} with {jd['file_name']}: {e}")
                    continue
        
        logger.info(f"Matching completed. {completed_matches} matches processed.")
        return results
    
    def generate_report(self, results):
        """Generate a summary report"""
        logger.info("Generating summary report...")
        
        if not results:
            logger.warning("No results to report")
            return
        
        # Calculate statistics
        total_matches = len(results)
        high_matches = len([r for r in results if r['verdict'] == 'High'])
        medium_matches = len([r for r in results if r['verdict'] == 'Medium'])
        low_matches = len([r for r in results if r['verdict'] == 'Low'])
        
        avg_score = sum(r['relevance_score'] for r in results) / total_matches
        
        # Find top matches
        top_matches = sorted(results, key=lambda x: x['relevance_score'], reverse=True)[:5]
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_matches': total_matches,
                'high_matches': high_matches,
                'medium_matches': medium_matches,
                'low_matches': low_matches,
                'average_score': round(avg_score, 2)
            },
            'top_matches': top_matches,
            'verdict_distribution': {
                'High': high_matches,
                'Medium': medium_matches,
                'Low': low_matches
            }
        }
        
        # Save report
        report_path = f"matching_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {report_path}")
        
        # Print summary
        print("\n" + "="*50)
        print("MATCHING SUMMARY REPORT")
        print("="*50)
        print(f"Total Matches: {total_matches}")
        print(f"High Matches: {high_matches} ({high_matches/total_matches*100:.1f}%)")
        print(f"Medium Matches: {medium_matches} ({medium_matches/total_matches*100:.1f}%)")
        print(f"Low Matches: {low_matches} ({low_matches/total_matches*100:.1f}%)")
        print(f"Average Score: {avg_score:.1f}%")
        print("\nTop 5 Matches:")
        for i, match in enumerate(top_matches, 1):
            print(f"{i}. {match['resume_name']} + {match['jd_name']}: {match['relevance_score']:.1f}% ({match['verdict']})")
        print("="*50)
        
        return report
    
    def run_complete_pipeline(self):
        """Run the complete pipeline"""
        logger.info("Starting complete resume relevance pipeline...")
        
        try:
            # Step 1: Extract and process files
            jd_processed, resume_processed = self.extract_and_process_files()
            
            if not jd_processed:
                logger.error("No job descriptions processed. Please check the JD folder.")
                return
            
            if not resume_processed:
                logger.error("No resumes processed. Please check the Resumes folder.")
                return
            
            # Step 2: Run matching
            results = self.run_matching(jd_processed, resume_processed)
            
            # Step 3: Generate report
            report = self.generate_report(results)
            
            logger.info("Pipeline completed successfully!")
            
            # Print database statistics
            stats = self.db_manager.get_statistics()
            print(f"\nDatabase Statistics:")
            print(f"Job Descriptions: {stats['job_descriptions']}")
            print(f"Resumes: {stats['resumes']}")
            print(f"Matching Results: {stats['matching_results']}")
            print(f"Average Score: {stats['average_score']}%")
            
            return report
        
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise


def main():
    """Main function"""
    print("Resume Relevance System - Simple Pipeline")
    print("=" * 50)
    
    # Check if data directories exist
    if not os.path.exists("data/JD"):
        print("Error: data/JD directory not found")
        return
    
    if not os.path.exists("data/Resumes"):
        print("Error: data/Resumes directory not found")
        return
    
    # Initialize and run pipeline
    pipeline = SimpleResumeRelevancePipeline()
    report = pipeline.run_complete_pipeline()
    
    if report:
        print("\n✅ Pipeline completed successfully!")
        print("You can now:")
        print("1. View the generated matching report JSON file")
        print("2. Check the database for detailed results")
        print("3. Start the API server: cd backend && python api.py")
        print("4. Start the dashboard: cd frontend && streamlit run app.py")
    else:
        print("\n❌ Pipeline failed. Please check the logs for details.")


if __name__ == "__main__":
    main()
