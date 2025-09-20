"""
Main Pipeline Script for Resume Relevance System
Processes existing datasets and runs the complete pipeline
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from utils.pdf_extractor import PDFExtractor
from utils.text_preprocessor import TextPreprocessor
from models.feature_engineering import FeatureEngineer
from models.relevance_scorer import RelevanceScorer
from utils.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ResumeRelevancePipeline:
    """Main pipeline for processing resumes and job descriptions"""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.text_preprocessor = TextPreprocessor()
        self.feature_engineer = FeatureEngineer()
        self.relevance_scorer = RelevanceScorer()
        self.db_manager = DatabaseManager()
        
        # Data paths
        self.jd_dir = "data/JD"
        self.resume_dir = "data/Resumes"
        
        logger.info("Pipeline initialized successfully")
    
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
                    # Calculate feature scores
                    feature_scores = self.feature_engineer.calculate_final_score(
                        resume['processed_data'], 
                        jd['processed_data']
                    )
                    
                    # Generate comprehensive analysis
                    analysis_result = self.relevance_scorer.generate_comprehensive_analysis(
                        resume['processed_data'], 
                        jd['processed_data'], 
                        feature_scores
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
                        'relevance_score': analysis_result['relevance_score'],
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
    print("Resume Relevance System - Complete Pipeline")
    print("=" * 50)
    
    # Check if data directories exist
    if not os.path.exists("data/JD"):
        print("Error: data/JD directory not found")
        return
    
    if not os.path.exists("data/Resumes"):
        print("Error: data/Resumes directory not found")
        return
    
    # Initialize and run pipeline
    pipeline = ResumeRelevancePipeline()
    report = pipeline.run_complete_pipeline()
    
    if report:
        print("\n✅ Pipeline completed successfully!")
        print("You can now:")
        print("1. Start the API server: cd backend && python api.py")
        print("2. Start the dashboard: cd frontend && streamlit run app.py")
        print("3. View results in the database or generated report")
    else:
        print("\n❌ Pipeline failed. Please check the logs for details.")


if __name__ == "__main__":
    main()
