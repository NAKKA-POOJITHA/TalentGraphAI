import time
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.embeddings.embedder import EmbeddingGenerator
from app.vector_db.chroma_service import ChromaService
from app.ranking.evaluator import CandidateEvaluator
from app.database.connection import get_db_cursor
from app.utils.logging import logger
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

router = APIRouter(prefix="/ranking", tags=["Ranking Engine"])

@router.post("/discover/{job_id}")
def discover_candidates(
    job_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Retrieve and rank candidates for a job using semantic search, growth velocity, and AI evaluation."""
    start_time = time.time()
    logger.info(f"Recruiter {current_user['email']} triggered discovery pipeline for job {job_id}")
    
    try:
        # 1. Fetch Job Description
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, title, cleaned_jd, extracted_metadata FROM jobs WHERE id = %s AND recruiter_id = %s", (job_id, current_user["id"]))
            job = cursor.fetchone()
            
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
            
        cleaned_jd = job["cleaned_jd"] or job["title"]
        
        # 2. Candidate Retrieval: Generate JD Embedding & Query ChromaDB
        retrieval_start = time.time()
        logger.info("Generating embedding for Job Description...")
        jd_embedding = EmbeddingGenerator.generate_embedding(cleaned_jd)
        
        logger.info("Querying ChromaDB for similar candidates...")
        similar_candidates = ChromaService.similarity_search(jd_embedding, limit=limit)
        retrieval_latency = time.time() - retrieval_start
        logger.info(f"Candidate retrieval completed in {retrieval_latency:.3f} seconds. Found {len(similar_candidates)} candidates.")
        
        if not similar_candidates:
            return {
                "job_id": job_id,
                "total_candidates": 0,
                "candidates": [],
                "metrics": {
                    "retrieval_latency_seconds": retrieval_latency,
                    "total_latency_seconds": time.time() - start_time
                }
            }
            
        # 3. AI Evaluation Pipeline (Concurrently execute Gemini & Growth scoring)
        evaluation_start = time.time()
        ranked_candidates = []
        
        # We will use ThreadPoolExecutor to run evaluations in parallel
        # Keep worker limit reasonable (e.g. 5) to avoid Gemini rate limit blocks
        max_workers = min(5, len(similar_candidates))
        logger.info(f"Starting concurrent candidate evaluations using {max_workers} worker threads...")
        
        def process_candidate(item):
            cand_id = item["candidate_id"]
            sim_score = item["similarity_score"]
            try:
                eval_res = CandidateEvaluator.evaluate_candidate_for_job(
                    candidate_id=cand_id,
                    job_id=job_id,
                    semantic_similarity_score=sim_score,
                    recruiter_id=current_user["id"]
                )
                return eval_res
            except Exception as e:
                logger.error(f"Failed to evaluate candidate {cand_id}: {e}")
                return None
                
        eval_results_map = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_cand = {
                executor.submit(process_candidate, item): item["candidate_id"]
                for item in similar_candidates
            }
            for future in as_completed(future_to_cand):
                cand_id = future_to_cand[future]
                try:
                    res = future.result()
                    if res:
                        eval_results_map[cand_id] = res
                except Exception as exc:
                    logger.error(f"Thread generated an exception for candidate {cand_id}: {exc}")

        # 4. Fetch Names & Emails for De-anonymized output
        candidate_ids = list(eval_results_map.keys())
        cand_info_map = {}
        if candidate_ids:
            with get_db_cursor() as cursor:
                # Direct SQL IN clause
                placeholders = ",".join(["%s"] * len(candidate_ids))
                cursor.execute(
                    f"SELECT id, name, email FROM candidates WHERE id IN ({placeholders})",
                    tuple(candidate_ids)
                )
                rows = cursor.fetchall()
                for row in rows:
                    cand_info_map[row["id"]] = row

        # 5. Compile and Sort Candidates by overall_score
        compiled_list = []
        for rank_idx, item in enumerate(similar_candidates):
            cand_id = item["candidate_id"]
            eval_data = eval_results_map.get(cand_id)
            if not eval_data:
                continue
                
            info = cand_info_map.get(cand_id, {"name": "Candidate", "email": ""})
            explain = eval_data["explainability"]
            
            compiled_list.append({
                "candidate_id": cand_id,
                "name": info["name"],
                "email": info["email"],
                "overall_score": eval_data["overall_score"],
                "semantic_score": explain["semantic_match"],
                "technical_score": explain["technical_match"],
                "domain_score": explain["domain_match"],
                "growth_score": explain["growth_velocity_score"],
                "growth_category": explain["growth_category"],
                "recommendation": explain["recommendation"],
                "explainability": explain,
                "bias_free_eval": eval_data["bias_free_eval"],
                "full_eval": eval_data["full_eval"]
            })
            
        # Sort descending by overall_score
        compiled_list.sort(key=lambda x: x["overall_score"], reverse=True)
        
        # Add ranks
        for idx, cand in enumerate(compiled_list):
            cand["rank"] = idx + 1
            
        evaluation_latency = time.time() - evaluation_start
        total_latency = time.time() - start_time
        
        logger.info(f"Job evaluation completed. Top candidate overall score: {compiled_list[0]['overall_score'] if compiled_list else 0}")
        return {
            "job_id": job_id,
            "total_candidates": len(compiled_list),
            "candidates": compiled_list,
            "metrics": {
                "retrieval_latency_seconds": round(retrieval_latency, 3),
                "evaluation_latency_seconds": round(evaluation_latency, 3),
                "total_latency_seconds": round(total_latency, 3)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in candidate discovery pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Candidate discovery failed: {str(e)}"
        )

@router.get("/history/{job_id}")
def get_ranking_history(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retrieve historical evaluations for a job."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT r.id, r.job_id, r.candidate_id, c.name, c.email, r.overall_score,
                       r.semantic_score, r.technical_score, r.domain_score, r.growth_score,
                       r.explainability, r.bias_free_eval, r.full_eval, r.created_at
                FROM ranking_history r
                JOIN candidates c ON r.candidate_id = c.id
                WHERE r.job_id = %s AND r.recruiter_id = %s
                ORDER BY r.overall_score DESC
                """,
                (job_id, current_user["id"])
            )
            history = cursor.fetchall()
            
        formatted_history = []
        for idx, row in enumerate(history):
            row_dict = dict(row)
            # Parse json fields
            for json_field in ["explainability", "bias_free_eval", "full_eval"]:
                if row_dict.get(json_field):
                    row_dict[json_field] = json.loads(row_dict[json_field]) if isinstance(row_dict[json_field], str) else row_dict[json_field]
            row_dict["rank"] = idx + 1
            formatted_history.append(row_dict)
            
        return formatted_history
        
    except Exception as e:
        logger.error(f"Failed to fetch ranking history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ranking history"
        )
