FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies needed for compiling certs and libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy NER model
RUN python -m spacy download en_core_web_sm

# Copy codebase
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
