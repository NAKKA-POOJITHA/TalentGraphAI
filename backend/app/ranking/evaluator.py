import json
from app.database.connection import get_db_cursor
from app.services.gemini import GeminiService
from app.ranking.bias import BiasReducer
from app.ranking.growth import GrowthVelocityEngine
from app.utils.logging import logger
from typing import Dict, Any

class CandidateEvaluator:
    @classmethod
    def evaluate_candidate_for_job(cls, candidate_id: str, job_id: str, semantic_similarity_score: float, recruiter_id: str) -> Dict[str, Any]:
        """Perform full ranking evaluation of a candidate against a job description."""
        logger.info(f"Evaluating candidate {candidate_id} for job {job_id}...")
        
        try:
            # 1. Fetch Candidate structured profile
            with get_db_cursor() as cursor:
                cursor.execute(
                    "SELECT c.name, c.email, r.parsed_json FROM candidates c JOIN resume_metadata r ON c.id = r.candidate_id WHERE c.id = %s",
                    (candidate_id,)
                )
                candidate_data = cursor.fetchone()
                
            if not candidate_data:
                raise Exception(f"Candidate {candidate_id} not found in database.")
                
            # Combine basic details and parsed JSON profile
            parsed_profile = candidate_data["parsed_json"]
            parsed_profile["name"] = candidate_data["name"]
            parsed_profile["email"] = candidate_data["email"]
            
            # 2. Fetch Job Description details
            with get_db_cursor() as cursor:
                cursor.execute("SELECT title, description, extracted_metadata FROM jobs WHERE id = %s", (job_id,))
                job_data = cursor.fetchone()
                
            if not job_data:
                raise Exception(f"Job {job_id} not found in database.")
                
            jd_metadata = job_data["extracted_metadata"] or {}
            # Fallback if metadata extraction was not done yet
            if not jd_metadata:
                jd_metadata = {"role": job_data["title"], "required_skills": [], "preferred_skills": []}

            # 3. Step A: Bias Reduction Module (Anonymization)
            anonymized_profile = BiasReducer.anonymize_profile(parsed_profile)
            
            # 4. Step B: Gemini Evaluation on anonymized profile
            logger.info("Requesting Gemini Evaluation for Anonymized candidate...")
            ai_eval = GeminiService.evaluate_candidate(anonymized_profile, jd_metadata)
            
            # 5. Step C: Professional Growth Velocity Scoring
            logger.info("Computing Professional Growth Velocity Score...")
            growth_details = GrowthVelocityEngine.calculate_growth_score(parsed_profile)
            growth_score = growth_details["growth_score"]
            
            # 6. final overall score calculation
            # Formula: 30% semantic similarity + 50% AI evaluation + 20% growth score
            semantic_score_100 = semantic_similarity_score * 100.0
            gemini_overall_score = float(ai_eval.get("overall_score", 50.0))
            
            final_overall_score = (semantic_score_100 * 0.30) + (gemini_overall_score * 0.50) + (growth_score * 0.20)
            final_overall_score = round(final_overall_score, 1)
            
            # 7. Create explainability and logs structure
            explainability = {
                "overall_score": final_overall_score,
                "strengths": ai_eval.get("strengths", []),
                "gaps": ai_eval.get("gaps", []),
                "reasoning": ai_eval.get("reasoning", ""),
                "recommendation": ai_eval.get("recommendation", "Not Recommended"),
                "confidence": ai_eval.get("confidence", 50.0),
                "semantic_match": round(semantic_score_100, 1),
                "technical_match": ai_eval.get("technical_score", 50.0),
                "domain_match": ai_eval.get("domain_score", 50.0),
                "growth_velocity_score": growth_score,
                "growth_category": growth_details["growth_category"],
                "growth_explanation": growth_details["explanation"]
            }
            
            # Log both evaluations for audit and explainability
            bias_free_eval = {
                "profile_sent": anonymized_profile,
                "evaluation_received": ai_eval
            }
            full_eval = {
                "profile_actual": parsed_profile,
                "growth_details": growth_details,
                "evaluation_received": ai_eval
            }
            
            # 8. Store results in ranking_history table
            logger.info("Storing evaluation results in Supabase ranking_history...")
            with get_db_cursor() as cursor:
                # Check if evaluation already exists for this job & candidate
                cursor.execute(
                    "SELECT id FROM ranking_history WHERE job_id = %s AND candidate_id = %s",
                    (job_id, candidate_id)
                )
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute(
                        """
                        UPDATE ranking_history SET
                            overall_score = %s,
                            semantic_score = %s,
                            technical_score = %s,
                            domain_score = %s,
                            growth_score = %s,
                            bias_free_eval = %s,
                            full_eval = %s,
                            explainability = %s,
                            created_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (
                            final_overall_score,
                            round(semantic_score_100, 1),
                            ai_eval.get("technical_score", 50.0),
                            ai_eval.get("domain_score", 50.0),
                            growth_score,
                            json.dumps(bias_free_eval),
                            json.dumps(full_eval),
                            json.dumps(explainability),
                            existing["id"]
                        )
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO ranking_history (
                            job_id, candidate_id, recruiter_id, overall_score,
                            semantic_score, technical_score, domain_score, growth_score,
                            bias_free_eval, full_eval, explainability
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            job_id,
                            candidate_id,
                            recruiter_id,
                            final_overall_score,
                            round(semantic_score_100, 1),
                            ai_eval.get("technical_score", 50.0),
                            ai_eval.get("domain_score", 50.0),
                            growth_score,
                            json.dumps(bias_free_eval),
                            json.dumps(full_eval),
                            json.dumps(explainability)
                        )
                    )
                    
            logger.info(f"Evaluation complete for {candidate_id}. Overall Score: {final_overall_score}")
            return {
                "candidate_id": candidate_id,
                "overall_score": final_overall_score,
                "explainability": explainability,
                "bias_free_eval": bias_free_eval,
                "full_eval": full_eval
            }
            
        except Exception as e:
            logger.error(f"Error evaluating candidate {candidate_id}: {e}")
            raise e
