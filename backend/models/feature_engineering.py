"""
Feature Engineering for Resume-JD Matching
Implements hard matching and soft matching using embeddings
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import faiss
from fuzzywuzzy import fuzz, process
from typing import List, Dict, Tuple, Optional
import logging
import pickle
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Feature engineering for resume-JD matching"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.sentence_model = None
        self.tfidf_vectorizer = None
        self.faiss_index = None
        self.embeddings_cache = {}
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize sentence transformer and TF-IDF models"""
        try:
            self.sentence_model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded sentence transformer: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer: {e}")
            self.sentence_model = None
        
        # Initialize TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
    
    def hard_match_skills(self, resume_skills: List[str], jd_skills: List[str]) -> float:
        """Calculate hard match score for skills using fuzzy matching"""
        if not resume_skills or not jd_skills:
            return 0.0
        
        total_matches = 0
        total_jd_skills = len(jd_skills)
        
        for jd_skill in jd_skills:
            # Find best match in resume skills
            best_match = process.extractOne(
                jd_skill, 
                resume_skills, 
                scorer=fuzz.token_sort_ratio
            )
            
            if best_match and best_match[1] >= 80:  # 80% similarity threshold
                total_matches += 1
        
        return total_matches / total_jd_skills if total_jd_skills > 0 else 0.0
    
    def hard_match_education(self, resume_education: List[str], jd_education: List[str]) -> float:
        """Calculate hard match score for education"""
        if not resume_education or not jd_education:
            return 0.0
        
        # Convert to lowercase for comparison
        resume_edu_lower = [edu.lower() for edu in resume_education]
        jd_edu_lower = [edu.lower() for edu in jd_education]
        
        matches = 0
        for jd_edu in jd_edu_lower:
            for resume_edu in resume_edu_lower:
                if jd_edu in resume_edu or resume_edu in jd_edu:
                    matches += 1
                    break
        
        return matches / len(jd_education) if jd_education else 0.0
    
    def hard_match_experience(self, resume_years: Optional[int], jd_years: Optional[int]) -> float:
        """Calculate hard match score for experience years"""
        if resume_years is None or jd_years is None:
            return 0.0
        
        if resume_years >= jd_years:
            return 1.0
        else:
            # Partial credit for having some experience
            return resume_years / jd_years
    
    def hard_match_keywords(self, resume_text: str, jd_text: str) -> float:
        """Calculate hard match score using TF-IDF keyword matching"""
        try:
            # Fit TF-IDF on both texts
            combined_texts = [resume_text, jd_text]
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(combined_texts)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        
        except Exception as e:
            logger.error(f"TF-IDF matching failed: {e}")
            return 0.0
    
    def calculate_hard_match_score(self, resume_data: Dict, jd_data: Dict) -> float:
        """Calculate overall hard match score"""
        # Weighted combination of different hard match components
        weights = {
            'skills': 0.4,
            'education': 0.2,
            'experience': 0.2,
            'keywords': 0.2
        }
        
        scores = {
            'skills': self.hard_match_skills(
                resume_data.get('skills', []), 
                jd_data.get('skills', [])
            ),
            'education': self.hard_match_education(
                resume_data.get('education', []), 
                jd_data.get('education', [])
            ),
            'experience': self.hard_match_experience(
                resume_data.get('experience_years'), 
                jd_data.get('experience_years')
            ),
            'keywords': self.hard_match_keywords(
                resume_data.get('cleaned_text', ''), 
                jd_data.get('cleaned_text', '')
            )
        }
        
        # Calculate weighted average
        total_score = sum(weights[key] * scores[key] for key in weights)
        return min(total_score, 1.0)  # Cap at 1.0
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get sentence embedding for text"""
        if not self.sentence_model or not text.strip():
            return None
        
        # Check cache first
        text_hash = hash(text)
        if text_hash in self.embeddings_cache:
            return self.embeddings_cache[text_hash]
        
        try:
            embedding = self.sentence_model.encode(text)
            self.embeddings_cache[text_hash] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    def soft_match_semantic(self, resume_text: str, jd_text: str) -> float:
        """Calculate soft match score using semantic similarity"""
        resume_embedding = self.get_embedding(resume_text)
        jd_embedding = self.get_embedding(jd_text)
        
        if resume_embedding is None or jd_embedding is None:
            return 0.0
        
        # Calculate cosine similarity
        similarity = cosine_similarity(
            resume_embedding.reshape(1, -1), 
            jd_embedding.reshape(1, -1)
        )[0][0]
        
        return float(similarity)
    
    def soft_match_sections(self, resume_sections: Dict, jd_sections: Dict) -> float:
        """Calculate soft match score for individual sections"""
        if not resume_sections or not jd_sections:
            return 0.0
        
        section_scores = []
        
        # Compare relevant sections
        relevant_sections = ['experience', 'skills', 'education']
        
        for section in relevant_sections:
            if section in resume_sections and section in jd_sections:
                score = self.soft_match_semantic(
                    resume_sections[section], 
                    jd_sections[section]
                )
                section_scores.append(score)
        
        return np.mean(section_scores) if section_scores else 0.0
    
    def calculate_soft_match_score(self, resume_data: Dict, jd_data: Dict) -> float:
        """Calculate overall soft match score"""
        # Overall semantic similarity
        overall_score = self.soft_match_semantic(
            resume_data.get('cleaned_text', ''), 
            jd_data.get('cleaned_text', '')
        )
        
        # Section-wise similarity
        section_score = self.soft_match_sections(
            resume_data.get('sections', {}), 
            jd_data.get('sections', {})
        )
        
        # Weighted combination
        return 0.7 * overall_score + 0.3 * section_score
    
    def calculate_final_score(self, resume_data: Dict, jd_data: Dict) -> Dict[str, float]:
        """Calculate final relevance score combining hard and soft matches"""
        hard_score = self.calculate_hard_match_score(resume_data, jd_data)
        soft_score = self.calculate_soft_match_score(resume_data, jd_data)
        
        # Weighted final score: 60% hard match, 40% soft match
        final_score = 0.6 * hard_score + 0.4 * soft_score
        
        return {
            'hard_match_score': hard_score,
            'soft_match_score': soft_score,
            'final_score': final_score,
            'relevance_percentage': final_score * 100
        }
    
    def save_embeddings_cache(self, cache_path: str):
        """Save embeddings cache to disk"""
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)
            logger.info(f"Embeddings cache saved to {cache_path}")
        except Exception as e:
            logger.error(f"Failed to save embeddings cache: {e}")
    
    def load_embeddings_cache(self, cache_path: str):
        """Load embeddings cache from disk"""
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    self.embeddings_cache = pickle.load(f)
                logger.info(f"Embeddings cache loaded from {cache_path}")
        except Exception as e:
            logger.error(f"Failed to load embeddings cache: {e}")


def main():
    """Test the feature engineering"""
    engineer = FeatureEngineer()
    
    # Sample data
    resume_data = {
        'cleaned_text': 'Software engineer with 5 years Python experience, Django, Flask, AWS',
        'skills': ['python', 'django', 'flask', 'aws', 'docker'],
        'education': ['bachelor computer science', 'master software engineering'],
        'experience_years': 5,
        'sections': {
            'experience': '5 years Python development',
            'skills': 'Python, Django, Flask, AWS, Docker'
        }
    }
    
    jd_data = {
        'cleaned_text': 'Looking for Python developer with Django experience, 3+ years, AWS knowledge',
        'skills': ['python', 'django', 'aws'],
        'education': ['bachelor computer science'],
        'experience_years': 3,
        'sections': {
            'experience': '3+ years Python development',
            'skills': 'Python, Django, AWS'
        }
    }
    
    scores = engineer.calculate_final_score(resume_data, jd_data)
    print("Matching Scores:")
    for key, value in scores.items():
        print(f"{key}: {value:.3f}")


if __name__ == "__main__":
    main()
