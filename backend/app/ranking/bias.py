import copy
import re
from typing import Dict, Any, List

class BiasReducer:
    @staticmethod
    def anonymize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
        """Strip personally identifying information (PII) from candidate profile."""
        # Deep copy to avoid mutating the original dictionary
        anon_profile = copy.deepcopy(profile)
        
        # 1. Anonymize Name and Email
        anon_profile["name"] = "ANONYMOUS_CANDIDATE"
        anon_profile["email"] = "HIDDEN@TALENTGRAPH.AI"
        
        # 2. Anonymize Education: Strip institution names, keep only degrees and years
        if "education" in anon_profile and isinstance(anon_profile["education"], list):
            anon_education = []
            for edu in anon_profile["education"]:
                # Only keep degree and year, replace institution
                degree = edu.get("degree", "Degree Details")
                year = edu.get("year", "")
                anon_education.append({
                    "degree": degree,
                    "institution": "ANONYMOUS_INSTITUTION",
                    "year": year
                })
            anon_profile["education"] = anon_education
            
        # 3. Clean any mentions of specific locations or typical PII from description text if possible
        # Since projects contain descriptions, we do a simple regex scrub for common email or phone patterns
        if "projects" in anon_profile and isinstance(anon_profile["projects"], list):
            for proj in anon_profile["projects"]:
                if "description" in proj:
                    desc = proj["description"]
                    # Regex scrub phone numbers
                    desc = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', desc)
                    # Regex scrub email addresses
                    desc = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', desc)
                    proj["description"] = desc

        # Log both versions for auditability / explainability
        # We return the anonymized version to be used in Gemini evaluation
        return anon_profile
