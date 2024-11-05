from fastapi import FastAPI, UploadFile, HTTPException
from sentence_transformers import SentenceTransformer
import redis
import numpy as np
from unstructured.partition.pdf import partition_pdf
from redis_setup import *
import tempfile

app = FastAPI()


# Load the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')  # You can use any other pre-trained model from sentence-transformers


# Function to extract text using unstructured.io
def extract_text_chunks_unstructured(file: UploadFile, chunk_size=500) -> list:
    # Write the uploaded file to a temporary file on disk
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file.file.read())
        temp_path = temp_file.name

    # Use unstructured.io to read the file from disk
    elements = partition_pdf(temp_path)
    text = " ".join([element.text for element in elements if element.text])

    # Split the text into chunks
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks


@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile):
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Extract text from the PDF
    text = extract_text_chunks_unstructured(file)
    if not text:
        raise HTTPException(status_code=400, detail="Failed to extract text from PDF")

    # Create embeddings using SentenceTransformer
    embedding = model.encode(text)

    # Store the embedding in Redis (use a unique key)
    key = f"pdf:{file.filename}"
    redis_client.set(key, np.array(embedding).tobytes())
    
    return {"message": f"PDF '{file.filename}' processed and stored successfully!"} 
    
# Run with: uvicorn app:app --reload
