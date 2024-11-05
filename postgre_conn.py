import psycopg2
from fastapi import FastAPI, File, UploadFile
from unstructured.partition.pdf import partition_pdf
import io

app = FastAPI()

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="password",
        host="localhost",
        port=5433
    )

# Initialize the database and create the document table if it doesn't exist
def init_db():
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS document (
            doc_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            document TEXT NOT NULL
        );
        """)
        conn.commit()
    conn.close()

init_db()

# Helper function to extract text from a PDF using unstructured.io
def extract_text_from_pdf(pdf_file: UploadFile) -> str:
    pdf_content = pdf_file.file.read()
    pdf_file.file.seek(0)  # Reset file pointer for FastAPI's file handling

    # Convert the bytes to a file-like object
    pdf_stream = io.BytesIO(pdf_content)
    elements = partition_pdf(file=pdf_stream)
    text = "\n".join([str(element) for element in elements])
    return text

# API endpoint to upload a PDF, extract text, and store it in PostgreSQL
@app.post("/upload-pdf/")
async def upload_pdf(user_id: int, pdf_file: UploadFile = File(...)):
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(pdf_file)
    print(pdf_text)

    # Store in PostgreSQL
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO document (user_id, document) VALUES (%s, %s) RETURNING doc_id",
            (user_id, pdf_text)
        )
        doc_id = cur.fetchone()[0]  # Retrieve the auto-incremented doc_id
        conn.commit()
    conn.close()

    return {"message": "PDF uploaded and content stored successfully.", "doc_id": doc_id}

@app.post("/see_document/")
async def fetch_pdf(doc_id: int):
    # Store in PostgreSQL
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT DOCUMENT FROM DOCUMENT WHERE DOC_ID={doc_id}"
            
        )
        pdf_text=cur.fetchone()
        conn.commit()
    conn.close()

    return pdf_text