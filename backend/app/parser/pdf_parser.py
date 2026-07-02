import fitz  # PyMuPDF
import spacy
from typing import Dict, Any, List, Tuple
from app.services.gemini import GeminiService
from app.utils.logging import logger

# Load spaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    logger.error(f"Failed to load spaCy model 'en_core_web_sm': {e}")
    # Fallback to downloading or error handling
    raise e

class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extract text content from a PDF file using PyMuPDF."""
        try:
            logger.info(f"Extracting text from PDF: {pdf_path}")
            doc = fitz.open(pdf_path)
            full_text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                full_text += page.get_text()
            
            doc.close()
            logger.info(f"Successfully extracted {len(full_text)} characters from PDF.")
            return full_text
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {e}")
            raise Exception(f"PDF extraction failed: {e}")

    @staticmethod
    def run_spacy_ner(text: str) -> Dict[str, List[str]]:
        """Run spaCy Named Entity Recognition on extracted text."""
        try:
            logger.info("Running spaCy NER on resume text...")
            # Truncate text if extremely long to avoid performance hits
            doc = nlp(text[:50000])
            
            entities = {
                "PERSON": [],
                "ORG": [],
                "GPE": [],
                "DATE": []
            }
            
            for ent in doc.ents:
                if ent.label_ in entities:
                    # Avoid adding duplicates
                    clean_text = ent.text.strip().replace("\n", " ")
                    if clean_text and clean_text not in entities[ent.label_]:
                        entities[ent.label_].append(clean_text)
            
            # Keep top 15 entities per category to prevent token bloating
            for key in entities:
                entities[key] = entities[key][:15]
                
            logger.info(f"spaCy NER completed. Found ORGs: {len(entities['ORG'])}, PERSONs: {len(entities['PERSON'])}")
            return entities
        except Exception as e:
            logger.error(f"spaCy NER execution failed: {e}")
            return {"PERSON": [], "ORG": [], "GPE": [], "DATE": []}

    @classmethod
    def parse_resume(cls, pdf_path: str) -> Dict[str, Any]:
        """Full pipeline: Extract PDF text -> spaCy NER -> Gemini Structured JSON."""
        try:
            # 1. Extract text
            raw_text = cls.extract_text_from_pdf(pdf_path)
            if not raw_text.strip():
                raise Exception("The PDF file appears to be empty or contains non-extractable text (e.g. scanned image).")
            
            # 2. Run NER
            entities = cls.run_spacy_ner(raw_text)
            
            # 3. Request Gemini parsing
            logger.info("Sending parsed text and entities to Gemini Service...")
            structured_data = GeminiService.parse_resume_text(raw_text, entities)
            
            # Ensure the response has all required fields to avoid runtime key errors
            default_fields = {
                "name": "Unknown Candidate",
                "email": "",
                "skills": [],
                "experience_years": 0.0,
                "education": [],
                "companies": [],
                "certifications": [],
                "projects": [],
                "achievements": []
            }
            
            for field, default in default_fields.items():
                if field not in structured_data or structured_data[field] is None:
                    structured_data[field] = default
                    
            logger.info(f"Successfully structured resume for candidate: {structured_data.get('name')}")
            return structured_data
            
        except Exception as e:
            logger.error(f"Error parsing resume {pdf_path}: {e}")
            raise e
