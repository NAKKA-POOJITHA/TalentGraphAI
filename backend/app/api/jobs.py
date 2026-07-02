from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import JobCreate, JobOut
from app.api.deps import get_current_user
from app.services.gemini import GeminiService
from app.database.connection import get_db_cursor
from app.utils.logging import logger
from typing import List
import json

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(job_in: JobCreate, current_user: dict = Depends(get_current_user)):
    """Upload and parse a new Job Description."""
    logger.info(f"Recruiter {current_user['email']} uploading job: {job_in.title}")
    
    try:
        # 1. Analyze Job Description using Gemini
        logger.info("Parsing Job Description text using Gemini...")
        parsed_jd = GeminiService.parse_job_description(job_in.description)
        
        # Extract fields
        cleaned_jd = parsed_jd.get("cleaned_jd", job_in.description)
        
        # 2. Store job in Supabase PostgreSQL
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO jobs (recruiter_id, title, description, extracted_metadata, cleaned_jd)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, recruiter_id, title, description, extracted_metadata, cleaned_jd, created_at
                """,
                (
                    current_user["id"],
                    job_in.title,
                    job_in.description,
                    json.dumps(parsed_jd),
                    cleaned_jd
                )
            )
            job = cursor.fetchone()
            
        logger.info(f"Successfully created and stored Job: {job_in.title} (ID: {job['id']})")
        return dict(job)
        
    except Exception as e:
        logger.error(f"Failed to process job description: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Job Description: {str(e)}"
        )

@router.get("/", response_model=List[JobOut])
def list_jobs(current_user: dict = Depends(get_current_user)):
    """List all Job Descriptions uploaded by the recruiter."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, recruiter_id, title, description, extracted_metadata, cleaned_jd, created_at FROM jobs WHERE recruiter_id = %s ORDER BY created_at DESC",
                (current_user["id"],)
            )
            jobs = cursor.fetchall()
            
        return [dict(job) for job in jobs]
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch jobs"
        )

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, current_user: dict = Depends(get_current_user)):
    """Get details of a specific Job Description."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, recruiter_id, title, description, extracted_metadata, cleaned_jd, created_at FROM jobs WHERE id = %s AND recruiter_id = %s",
                (job_id, current_user["id"])
            )
            job = cursor.fetchone()
            
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
            
        return dict(job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job details"
        )

@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
def delete_job(job_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a Job Description and all its associated ranking history."""
    logger.info(f"Recruiter {current_user['email']} deleting job: {job_id}")
    try:
        with get_db_cursor() as cursor:
            # Check if job exists and belongs to current user
            cursor.execute("SELECT id FROM jobs WHERE id = %s AND recruiter_id = %s", (job_id, current_user["id"]))
            job = cursor.fetchone()
            if not job:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job description not found"
                )
            
            cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        logger.info(f"Successfully deleted Job: {job_id}")
        return {"status": "success", "message": "Job description deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )

