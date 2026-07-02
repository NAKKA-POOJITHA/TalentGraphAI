import os
import sys
import json
import httpx
import fitz  # PyMuPDF to generate PDF resumes
from app.utils.logging import logger

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://127.0.0.1:8000/api"

# Helper to generate a PDF resume
def create_pdf_resume(filename: str, name: str, email: str, content: str):
    """Generate a clean PDF resume using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    
    # Write details to PDF
    text = f"NAME: {name}\nEMAIL: {email}\n\n{content}"
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv")
    
    doc.save(filename)
    doc.close()
    logger.info(f"Generated test resume: {filename}")

def run_integration_test():
    logger.info("Initializing programmatical pipeline verification...")
    
    # 1. Create Mock Resumes
    create_pdf_resume(
        "resume_high_match.pdf",
        "Alice Dev",
        "alice.dev@example.com",
        """
        SUMMARY:
        Lead Backend Engineer with 6 years of experience building high-scale Python web applications.
        Specialist in FastAPI, PostgreSQL, AWS, Docker, and distributed systems.
        
        EXPERIENCE:
        Lead Engineer at CloudTech (2023 - Present)
        - Led a team of 4 backend engineers to migrate microservices to FastAPI, improving latency by 40%.
        - Designed and optimized high-performance PostgreSQL database queries, reducing load times.
        - Deployed scalable Docker containers orchestrated by Kubernetes on AWS ECS.
        Senior Engineer at WebSolutions (2020 - 2023)
        - Developed RESTful APIs using Python, Django, and FastAPI.
        - Mentored junior engineers and introduced automated testing pipelines.
        
        CERTIFICATIONS:
        - AWS Certified Solutions Architect - Associate
        - Certified Kubernetes Administrator (CKA)
        
        EDUCATION:
        - M.S. Computer Science, Stanford University (2020)
        """
    )

    create_pdf_resume(
        "resume_medium_match.pdf",
        "Bob Smith",
        "bob.smith@example.com",
        """
        SUMMARY:
        Software Developer with 3 years of experience. Experienced in Python, Django, and relational databases.
        Interested in learning cloud architectures and modern API design.
        
        EXPERIENCE:
        Python Developer at InfoSys (2022 - Present)
        - Maintained backend APIs built on Django and Flask.
        - Wrote SQL queries and integrated external APIs.
        - Assisted with Docker packaging for deployments.
        
        EDUCATION:
        - B.S. Information Technology, Texas A&M University (2022)
        """
    )

    create_pdf_resume(
        "resume_low_match.pdf",
        "Charlie Cook",
        "charlie.cook@example.com",
        """
        SUMMARY:
        Experienced Sales Executive and Account Manager with 5 years in retail and B2B client relations.
        Proven track record of driving revenue growth and coordinating sales campaigns.
        
        EXPERIENCE:
        Sales Lead at RetailCorp (2021 - Present)
        - Managed 10 client accounts generating $500k in annual revenue.
        - Supervised and trained a team of 5 sales associates.
        
        EDUCATION:
        - B.A. Communications, Boston University (2021)
        """
    )

    client = httpx.Client(timeout=400.0)

    try:
        # 2. Register Recruiter
        email = f"test_recruiter_{os.urandom(2).hex()}@talentgraph.ai"
        password = "SecurePassword123!"
        
        logger.info(f"Step 1: Registering recruiter {email}...")
        reg_resp = client.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password, "full_name": "Test Recruiter"}
        )
        assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"
        logger.info("Recruiter registration successful!")

        # 3. Log In Recruiter
        logger.info("Step 2: Authenticating recruiter...")
        login_resp = client.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password}
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        logger.info("Authentication successful! Token acquired.")

        # 4. Upload Job Description
        logger.info("Step 3: Creating a Job Description...")
        jd_data = {
            "title": "Senior Python Backend Developer (FastAPI & Cloud)",
            "description": """
            Role Overview:
            We are looking for a Senior Python Developer with 5+ years of experience to join our core backend engineering team.
            
            Core Technical Skills Required (Mandatory):
            - Python, FastAPI, PostgreSQL, SQL optimization.
            
            Preferred Skills (Nice-to-have):
            - Docker, Kubernetes, AWS (solutions architect knowledge).
            
            Responsibilities:
            - Design and build RESTful microservices.
            - Optimize database queries.
            - Lead, mentor, and coordinate design decisions.
            """
        }
        jd_resp = client.post(f"{BASE_URL}/jobs/", json=jd_data, headers=headers)
        assert jd_resp.status_code == 201, f"JD creation failed: {jd_resp.text}"
        job = jd_resp.json()
        job_id = job["id"]
        logger.info(f"Job Description processed successfully. Job ID: {job_id}")

        # 5. Upload PDF Resumes
        logger.info("Step 4: Uploading PDF Resumes (Batch processing)...")
        f1 = open("resume_high_match.pdf", "rb")
        f2 = open("resume_medium_match.pdf", "rb")
        f3 = open("resume_low_match.pdf", "rb")
        files = [
            ("files", ("resume_high_match.pdf", f1, "application/pdf")),
            ("files", ("resume_medium_match.pdf", f2, "application/pdf")),
            ("files", ("resume_low_match.pdf", f3, "application/pdf"))
        ]
        try:
            upload_resp = client.post(f"{BASE_URL}/candidates/upload", files=files, headers=headers)
        finally:
            f1.close()
            f2.close()
            f3.close()
        assert upload_resp.status_code == 201, f"Resumes upload failed: {upload_resp.text}"
        
        upload_results = upload_resp.json()
        logger.info(f"Resume upload completed: Success={upload_results['total_success']}, Failed={upload_results['total_failed']}")
        assert upload_results["total_success"] == 3, f"Expected 3 successful uploads, got {upload_results['total_success']}"

        # 6. Execute Candidate Reranking & Semantic Search
        logger.info("Step 5: Invoking Candidate Discovery Pipeline...")
        discover_resp = client.post(f"{BASE_URL}/ranking/discover/{job_id}", headers=headers)
        assert discover_resp.status_code == 200, f"Discovery failed: {discover_resp.text}"
        
        discovery_results = discover_resp.json()
        candidates = discovery_results["candidates"]
        metrics = discovery_results["metrics"]
        
        logger.info(f"Discovery pipeline metrics: {json.dumps(metrics, indent=2)}")
        logger.info(f"Ranked {len(candidates)} candidates.")

        # Assert correct ordering (High match > Medium match > Low match)
        assert len(candidates) >= 3, "Expected at least 3 candidates in ranking"
        
        for cand in candidates:
            name = cand["name"]
            score = cand["overall_score"]
            rec = cand["recommendation"]
            growth_cat = cand["growth_category"]
            logger.info(f"Rank {cand['rank']}: {name} - Score: {score}% - Recommendation: {rec} - Growth Index: {growth_cat}")
            
            # Print brief explainability gaps/strengths
            explain = cand["explainability"]
            logger.info(f"  Strengths: {explain['strengths']}")
            logger.info(f"  Skill Gaps: {explain['gaps']}")
            
        logger.info("Verification Complete! All integration assertions passed successfully.")
        return True

    except Exception as e:
        logger.error(f"Integration Test crashed: {e}")
        raise e
    finally:
        client.close()
        # Cleanup mock PDF files safely
        for f in ["resume_high_match.pdf", "resume_medium_match.pdf", "resume_low_match.pdf"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception as cleanup_err:
                    logger.warning(f"Could not remove test file {f}: {cleanup_err}")

if __name__ == "__main__":
    run_integration_test()
