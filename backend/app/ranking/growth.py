from typing import Dict, Any, List
from app.utils.logging import logger

class GrowthVelocityEngine:
    @classmethod
    def calculate_growth_score(cls, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the professional growth velocity score of a candidate."""
        try:
            skills = profile.get("skills", [])
            experience_years = float(profile.get("experience_years", 0))
            projects = profile.get("projects", [])
            certifications = profile.get("certifications", [])
            education = profile.get("education", [])
            companies = profile.get("companies", [])
            
            # --- 1. Promotion Frequency (30% weight) ---
            # Approximated by the number of companies/roles transitions relative to experience years
            transitions = len(companies) + len(projects)
            if experience_years <= 0:
                promotion_frequency = 50.0  # Base line score for freshers
            else:
                # Target ratio: 1.5 career updates/projects per year
                ratio = transitions / max(1.0, experience_years)
                promotion_frequency = min(100.0, ratio * 40.0)
                # Keep a minimum baseline of 40 if they have experience
                promotion_frequency = max(40.0, promotion_frequency)

            # --- 2. Skill Expansion (25% weight) ---
            # Based on the size of the technical toolkit and project diversity
            skills_count = len(skills)
            skill_expansion = min(100.0, skills_count * 5.0)  # 20 skills = 100
            skill_expansion = max(30.0, skill_expansion) # Baseline

            # --- 3. Project Complexity (20% weight) ---
            # Evaluated by looking at projects count and tech usage
            project_count = len(projects)
            complexity_score = min(100.0, project_count * 20.0)
            
            # Add boost for projects that have description detailing complex topics
            complex_keywords = ["scale", "optimize", "architect", "redesign", "distribute", "cloud", "security", "pipeline", "performance"]
            boost = 0
            for proj in projects:
                desc = (proj.get("description") or "").lower()
                for keyword in complex_keywords:
                    if keyword in desc:
                        boost += 3
            complexity_score = min(100.0, complexity_score + boost)
            complexity_score = max(30.0, complexity_score)

            # --- 4. Certification Growth (15% weight) ---
            # Based on professional certifications obtained
            cert_count = len(certifications)
            certification_growth = min(100.0, cert_count * 25.0) # 4 certs = 100
            # If no certs, check if they have master's degree or higher for partial score
            if certification_growth == 0:
                has_advanced_edu = any("master" in str(edu.get("degree") or "").lower() or "phd" in str(edu.get("degree") or "").lower() for edu in education)
                if has_advanced_edu:
                    certification_growth = 50.0
                else:
                    certification_growth = 20.0 # Baseline

            # --- 5. Leadership (10% weight) ---
            # Scans projects for leadership keywords (Lead, Senior, Coordinate, Mentor, Manage, Architect)
            leadership_score = 40.0 # Base score
            leadership_terms = ["lead", "senior", "coordinator", "mentor", "manage", "architect", "head", "founder", "director", "principal"]
            
            # Check in project roles or project descriptions
            for proj in projects:
                role = (proj.get("role") or "").lower()
                desc = (proj.get("description") or "").lower()
                if any(term in role for term in leadership_terms) or any(term in desc for term in leadership_terms):
                    leadership_score = min(100.0, leadership_score + 20.0)
            
            # Apply Weighted Growth Formula
            growth_score = (
                (promotion_frequency * 0.30) +
                (skill_expansion * 0.25) +
                (complexity_score * 0.20) +
                (certification_growth * 0.15) +
                (leadership_score * 0.10)
            )
            
            # Map score to Category
            if growth_score >= 80.0:
                growth_category = "High"
                explanation = f"Candidate displays rapid career growth velocity (Score: {growth_score:.1f}/100) with frequent projects/role transitions, a wide technical toolset, and strong leadership/complexity indicators."
            elif growth_score >= 50.0:
                growth_category = "Medium"
                explanation = f"Candidate shows steady career progression (Score: {growth_score:.1f}/100). They have regular work updates and structured skillset expansion aligned with standard career paths."
            else:
                growth_category = "Low"
                explanation = f"Candidate growth index is moderate (Score: {growth_score:.1f}/100). It suggests specialized stability in roles, with fewer project rotations or cert acquisitions."

            return {
                "growth_score": round(growth_score, 1),
                "growth_category": growth_category,
                "promotion_frequency": round(promotion_frequency, 1),
                "skill_expansion": round(skill_expansion, 1),
                "project_complexity": round(complexity_score, 1),
                "certification_growth": round(certification_growth, 1),
                "leadership": round(leadership_score, 1),
                "explanation": explanation
            }
            
        except Exception as e:
            logger.error(f"Error calculating growth velocity: {e}")
            return {
                "growth_score": 50.0,
                "growth_category": "Medium",
                "promotion_frequency": 50.0,
                "skill_expansion": 50.0,
                "project_complexity": 50.0,
                "certification_growth": 50.0,
                "leadership": 50.0,
                "explanation": "Calculated default medium growth due to error."
            }
            
            
def calculate_growth_score(profile: Dict[str, Any]) -> Dict[str, Any]:
    return GrowthVelocityEngine.calculate_growth_score(profile)
