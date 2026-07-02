from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from app.api.deps import get_current_user
from app.parser.pdf_parser import ResumeParser
from app.embeddings.embedder import EmbeddingGenerator
from app.vector_db.chroma_service import ChromaService
from app.database.connection import get_db_cursor
from app.utils.config import settings
from app.utils.logging import logger
from typing import List, Dict, Any
import os
import uuid
import json

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resumes(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload multiple PDF resumes, parse metadata, generate embeddings, and index them in ChromaDB."""
    logger.info(f"Recruiter {current_user['email']} uploading {len(files)} resume files.")
    
    success_list = []
    failure_list = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            failure_list.append({
                "filename": file.filename,
                "error": "Only PDF files are supported"
            })
            continue
            
        try:
            # 1. Save uploaded file locally
            file_id = str(uuid.uuid4())
            safe_filename = f"{file_id}_{file.filename}"
            filepath = os.path.join(settings.UPLOAD_DIR, safe_filename)
            
            with open(filepath, "wb") as f:
                content = await file.read()
                f.write(content)
                
            # 2. Extract plain text from PDF
            raw_text = ResumeParser.extract_text_from_pdf(filepath)
            
            # 3. Parse resume text using PyMuPDF + spaCy + Gemini
            logger.info(f"Parsing resume structure for {file.filename}...")
            parsed_profile = ResumeParser.parse_resume(filepath)
            
            candidate_name = parsed_profile.get("name", "Unknown Candidate")
            candidate_email = parsed_profile.get("email", None)
            
            # 4. Generate embeddings (using raw_text for max semantic density)
            logger.info(f"Generating embedding for candidate resume text...")
            embedding = EmbeddingGenerator.generate_embedding(raw_text)
            
            # 5. Save to Supabase SQL
            logger.info(f"Saving candidate details to PostgreSQL database...")
            with get_db_cursor() as cursor:
                # Insert candidate main record
                cursor.execute(
                    """
                    INSERT INTO candidates (id, recruiter_id, name, email, resume_url, original_pdf_path)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, name, email, created_at
                    """,
                    (
                        file_id,
                        current_user["id"],
                        candidate_name,
                        candidate_email,
                        f"/static/{safe_filename}", # mock resume url
                        filepath
                    )
                )
                candidate = cursor.fetchone()
                
                # Insert resume metadata
                cursor.execute(
                    """
                    INSERT INTO resume_metadata (
                        candidate_id, skills, experience_years, education,
                        companies, certifications, projects, achievements, parsed_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        file_id,
                        parsed_profile.get("skills", []),
                        parsed_profile.get("experience_years", 0.0),
                        json.dumps(parsed_profile.get("education", [])),
                        parsed_profile.get("companies", []),
                        parsed_profile.get("certifications", []),
                        json.dumps(parsed_profile.get("projects", [])),
                        parsed_profile.get("achievements", []),
                        json.dumps(parsed_profile)
                    )
                )
                
                # Save embedding reference mapping
                cursor.execute(
                    """
                    INSERT INTO candidate_embeddings (candidate_id, chroma_id)
                    VALUES (%s, %s)
                    """,
                    (file_id, file_id)
                )
                
            # 6. Index embedding inside ChromaDB
            logger.info("Indexing candidate vector inside ChromaDB persistence...")
            chroma_metadata = {
                "candidate_id": file_id,
                "skills": parsed_profile.get("skills", []),
                "experience_years": parsed_profile.get("experience_years", 0.0),
                "companies": parsed_profile.get("companies", []),
                "certifications": parsed_profile.get("certifications", [])
            }
            
            ChromaService.insert_candidate(
                candidate_id=file_id,
                embedding=embedding,
                metadata=chroma_metadata,
                document_text=raw_text
            )
            
            success_list.append({
                "candidate_id": file_id,
                "name": candidate_name,
                "email": candidate_email,
                "filename": file.filename,
                "status": "Successfully uploaded and parsed"
            })
            
        except Exception as e:
            logger.error(f"Failed to process file {file.filename}: {e}")
            failure_list.append({
                "filename": file.filename,
                "error": str(e)
            })
            
    return {
        "success": success_list,
        "failures": failure_list,
        "total_success": len(success_list),
        "total_failed": len(failure_list)
    }

@router.get("/")
def list_candidates(current_user: dict = Depends(get_current_user)):
    """List all parsed candidates for the active recruiter."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT c.id, c.recruiter_id, c.name, c.email, c.resume_url, c.original_pdf_path, c.created_at,
                       r.skills, r.experience_years, r.education, r.companies, r.certifications, r.projects, r.achievements
                FROM candidates c
                LEFT JOIN resume_metadata r ON c.id = r.candidate_id
                WHERE c.recruiter_id = %s
                ORDER BY c.created_at DESC
                """,
                (current_user["id"],)
            )
            candidates = cursor.fetchall()
            
        formatted_candidates = []
        for cand in candidates:
            cand_dict = dict(cand)
            # Parse json fields
            if cand_dict.get("education"):
                cand_dict["education"] = json.loads(cand_dict["education"]) if isinstance(cand_dict["education"], str) else cand_dict["education"]
            if cand_dict.get("projects"):
                cand_dict["projects"] = json.loads(cand_dict["projects"]) if isinstance(cand_dict["projects"], str) else cand_dict["projects"]
            formatted_candidates.append(cand_dict)
            
        return formatted_candidates
    except Exception as e:
        logger.error(f"Error listing candidates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve candidates"
        )

@router.get("/{candidate_id}")
def get_candidate(candidate_id: str, current_user: dict = Depends(get_current_user)):
    """Get details of a specific candidate."""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT c.id, c.recruiter_id, c.name, c.email, c.resume_url, c.original_pdf_path, c.created_at,
                       r.skills, r.experience_years, r.education, r.companies, r.certifications, r.projects, r.achievements, r.parsed_json
                FROM candidates c
                LEFT JOIN resume_metadata r ON c.id = r.candidate_id
                WHERE c.id = %s AND c.recruiter_id = %s
                """,
                (candidate_id, current_user["id"])
            )
            cand = cursor.fetchone()
            
        if not cand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
            
        cand_dict = dict(cand)
        if cand_dict.get("education"):
            cand_dict["education"] = json.loads(cand_dict["education"]) if isinstance(cand_dict["education"], str) else cand_dict["education"]
        if cand_dict.get("projects"):
            cand_dict["projects"] = json.loads(cand_dict["projects"]) if isinstance(cand_dict["projects"], str) else cand_dict["projects"]
        if cand_dict.get("parsed_json"):
            cand_dict["parsed_json"] = json.loads(cand_dict["parsed_json"]) if isinstance(cand_dict["parsed_json"], str) else cand_dict["parsed_json"]
            
        return cand_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching candidate details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch candidate details"
        )

@router.delete("/{candidate_id}", status_code=status.HTTP_200_OK)
def delete_candidate(candidate_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a candidate resume, its vector embeddings, and the uploaded file."""
    logger.info(f"Recruiter {current_user['email']} deleting candidate: {candidate_id}")
    try:
        with get_db_cursor() as cursor:
            # Check if candidate exists and belongs to current user
            cursor.execute("SELECT id, original_pdf_path FROM candidates WHERE id = %s AND recruiter_id = %s", (candidate_id, current_user["id"]))
            cand = cursor.fetchone()
            if not cand:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Candidate not found"
                )
            
            pdf_path = cand["original_pdf_path"]
            
            # Delete from DB
            cursor.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
            
        # Delete from ChromaDB
        try:
            ChromaService.delete_candidate(candidate_id)
        except Exception as e:
            logger.warning(f"Failed to delete candidate {candidate_id} from ChromaDB: {e}")
            
        # Delete PDF file
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception as e:
                logger.warning(f"Failed to delete file {pdf_path}: {e}")
                
        logger.info(f"Successfully deleted candidate: {candidate_id}")
        return {"status": "success", "message": "Candidate resume deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete candidate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete candidate: {str(e)}"
        )

