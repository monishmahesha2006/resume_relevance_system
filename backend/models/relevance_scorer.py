"""
Relevance Scoring Algorithm
Implements weighted scoring and generates feedback
"""

import openai
from typing import Dict, List, Optional, Tuple
import logging
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RelevanceScorer:
    """Calculate relevance scores and generate feedback"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Scoring thresholds
        self.thresholds = {
            'high': 0.75,
            'medium': 0.50,
            'low': 0.25
        }
    
    def calculate_relevance_score(self, feature_scores: Dict[str, float]) -> Dict[str, any]:
        """Calculate final relevance score and verdict"""
        final_score = feature_scores.get('final_score', 0.0)
        relevance_percentage = final_score * 100
        
        # Determine suitability verdict
        if final_score >= self.thresholds['high']:
            verdict = 'High'
        elif final_score >= self.thresholds['medium']:
            verdict = 'Medium'
        else:
            verdict = 'Low'
        
        return {
            'relevance_score': relevance_percentage,
            'verdict': verdict,
            'hard_match_score': feature_scores.get('hard_match_score', 0.0),
            'soft_match_score': feature_scores.get('soft_match_score', 0.0),
            'final_score': final_score
        }
    
    def identify_missing_skills(self, resume_skills: List[str], jd_skills: List[str]) -> List[str]:
        """Identify skills that are in JD but missing from resume"""
        missing_skills = []
        
        for jd_skill in jd_skills:
            jd_skill_lower = jd_skill.lower()
            found = False
            
            for resume_skill in resume_skills:
                resume_skill_lower = resume_skill.lower()
                # Check for exact match or partial match
                if (jd_skill_lower == resume_skill_lower or 
                    jd_skill_lower in resume_skill_lower or 
                    resume_skill_lower in jd_skill_lower):
                    found = True
                    break
            
            if not found:
                missing_skills.append(jd_skill)
        
        return missing_skills
    
    def identify_missing_education(self, resume_education: List[str], jd_education: List[str]) -> List[str]:
        """Identify education requirements that are missing"""
        missing_education = []
        
        for jd_edu in jd_education:
            jd_edu_lower = jd_edu.lower()
            found = False
            
            for resume_edu in resume_education:
                resume_edu_lower = resume_edu.lower()
                if (jd_edu_lower in resume_edu_lower or 
                    resume_edu_lower in jd_edu_lower):
                    found = True
                    break
            
            if not found:
                missing_education.append(jd_edu)
        
        return missing_education
    
    def check_experience_gap(self, resume_years: Optional[int], jd_years: Optional[int]) -> Dict[str, any]:
        """Check experience requirements gap"""
        if resume_years is None or jd_years is None:
            return {'gap': 0, 'meets_requirement': True, 'message': 'Experience requirements not specified'}
        
        gap = jd_years - resume_years
        meets_requirement = resume_years >= jd_years
        
        if gap > 0:
            message = f"Missing {gap} years of experience"
        elif gap == 0:
            message = "Meets experience requirement exactly"
        else:
            message = f"Exceeds requirement by {abs(gap)} years"
        
        return {
            'gap': gap,
            'meets_requirement': meets_requirement,
            'message': message
        }
    
    def generate_llm_feedback(self, resume_data: Dict, jd_data: Dict, scores: Dict) -> str:
        """Generate personalized feedback using LLM"""
        if not self.openai_api_key:
            return self._generate_basic_feedback(resume_data, jd_data, scores)
        
        try:
            prompt = self._create_feedback_prompt(resume_data, jd_data, scores)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a career counselor providing constructive feedback on resume-JD matching."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"LLM feedback generation failed: {e}")
            return self._generate_basic_feedback(resume_data, jd_data, scores)
    
    def _create_feedback_prompt(self, resume_data: Dict, jd_data: Dict, scores: Dict) -> str:
        """Create prompt for LLM feedback generation"""
        prompt = f"""
        Analyze this resume-JD match and provide constructive feedback:
        
        Job Requirements:
        - Skills: {', '.join(jd_data.get('skills', []))}
        - Education: {', '.join(jd_data.get('education', []))}
        - Experience: {jd_data.get('experience_years', 'Not specified')} years
        
        Candidate Profile:
        - Skills: {', '.join(resume_data.get('skills', []))}
        - Education: {', '.join(resume_data.get('education', []))}
        - Experience: {resume_data.get('experience_years', 'Not specified')} years
        
        Match Score: {scores.get('relevance_score', 0):.1f}% ({scores.get('verdict', 'Unknown')})
        
        Provide 2-3 specific, actionable suggestions for improvement.
        """
        return prompt
    
    def _generate_basic_feedback(self, resume_data: Dict, jd_data: Dict, scores: Dict) -> str:
        """Generate basic feedback without LLM"""
        feedback_parts = []
        
        # Check missing skills
        missing_skills = self.identify_missing_skills(
            resume_data.get('skills', []), 
            jd_data.get('skills', [])
        )
        
        if missing_skills:
            feedback_parts.append(f"Consider adding these skills: {', '.join(missing_skills[:3])}")
        
        # Check experience gap
        exp_gap = self.check_experience_gap(
            resume_data.get('experience_years'), 
            jd_data.get('experience_years')
        )
        
        if not exp_gap['meets_requirement']:
            feedback_parts.append(exp_gap['message'])
        
        # Check education
        missing_education = self.identify_missing_education(
            resume_data.get('education', []), 
            jd_data.get('education', [])
        )
        
        if missing_education:
            feedback_parts.append(f"Consider highlighting relevant education: {', '.join(missing_education)}")
        
        # General advice based on score
        if scores.get('relevance_score', 0) < 50:
            feedback_parts.append("Focus on aligning your skills and experience more closely with the job requirements")
        elif scores.get('relevance_score', 0) < 75:
            feedback_parts.append("Good match overall, but there's room for improvement in specific areas")
        else:
            feedback_parts.append("Strong match! Consider highlighting your most relevant achievements")
        
        return ". ".join(feedback_parts) + "."
    
    def generate_comprehensive_analysis(self, resume_data: Dict, jd_data: Dict, feature_scores: Dict) -> Dict[str, any]:
        """Generate comprehensive analysis of resume-JD match"""
        
        # Calculate relevance score
        relevance_result = self.calculate_relevance_score(feature_scores)
        
        # Identify gaps
        missing_skills = self.identify_missing_skills(
            resume_data.get('skills', []), 
            jd_data.get('skills', [])
        )
        
        missing_education = self.identify_missing_education(
            resume_data.get('education', []), 
            jd_data.get('education', [])
        )
        
        experience_analysis = self.check_experience_gap(
            resume_data.get('experience_years'), 
            jd_data.get('experience_years')
        )
        
        # Generate feedback
        feedback = self.generate_llm_feedback(resume_data, jd_data, relevance_result)
        
        return {
            'relevance_score': relevance_result['relevance_score'],
            'verdict': relevance_result['verdict'],
            'hard_match_score': relevance_result['hard_match_score'],
            'soft_match_score': relevance_result['soft_match_score'],
            'missing_skills': missing_skills,
            'missing_education': missing_education,
            'experience_analysis': experience_analysis,
            'feedback': feedback,
            'strengths': self._identify_strengths(resume_data, jd_data),
            'improvement_areas': self._identify_improvement_areas(resume_data, jd_data)
        }
    
    def _identify_strengths(self, resume_data: Dict, jd_data: Dict) -> List[str]:
        """Identify candidate strengths"""
        strengths = []
        
        # Skills match
        resume_skills = resume_data.get('skills', [])
        jd_skills = jd_data.get('skills', [])
        
        matching_skills = []
        for jd_skill in jd_skills:
            for resume_skill in resume_skills:
                if (jd_skill.lower() in resume_skill.lower() or 
                    resume_skill.lower() in jd_skill.lower()):
                    matching_skills.append(resume_skill)
                    break
        
        if matching_skills:
            strengths.append(f"Strong technical skills: {', '.join(matching_skills[:3])}")
        
        # Experience
        resume_years = resume_data.get('experience_years', 0)
        jd_years = jd_data.get('experience_years', 0)
        
        if resume_years and jd_years and resume_years >= jd_years:
            strengths.append(f"Meets experience requirement ({resume_years} years)")
        
        return strengths
    
    def _identify_improvement_areas(self, resume_data: Dict, jd_data: Dict) -> List[str]:
        """Identify areas for improvement"""
        areas = []
        
        # Missing skills
        missing_skills = self.identify_missing_skills(
            resume_data.get('skills', []), 
            jd_data.get('skills', [])
        )
        
        if missing_skills:
            areas.append(f"Develop missing skills: {', '.join(missing_skills[:3])}")
        
        # Experience gap
        exp_gap = self.check_experience_gap(
            resume_data.get('experience_years'), 
            jd_data.get('experience_years')
        )
        
        if not exp_gap['meets_requirement']:
            areas.append(exp_gap['message'])
        
        return areas


def main():
    """Test the relevance scorer"""
    scorer = RelevanceScorer()
    
    # Sample data
    resume_data = {
        'skills': ['python', 'django', 'flask'],
        'education': ['bachelor computer science'],
        'experience_years': 3
    }
    
    jd_data = {
        'skills': ['python', 'django', 'aws', 'docker'],
        'education': ['bachelor computer science'],
        'experience_years': 5
    }
    
    feature_scores = {
        'final_score': 0.65,
        'hard_match_score': 0.6,
        'soft_match_score': 0.7
    }
    
    analysis = scorer.generate_comprehensive_analysis(resume_data, jd_data, feature_scores)
    
    print("Comprehensive Analysis:")
    for key, value in analysis.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
