import io
import psycopg2
from fastapi import FastAPI, File, UploadFile, HTTPException
from unstructured.partition.pdf import partition_pdf
from chromadb import Client
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

app = FastAPI()

##llm object
llm = ChatGroq(
    model="llama-3.1-70b-versatile",
    temperature=0.0,
    groq_api_key="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"
    # other params...
)

res=llm.invoke("Who is the prime minister of India?")

# Initialize ChromaDB client and collection
chroma_client = Client(Settings(persist_directory="chroma_storage"))
collection_name = "documents_collection"
if collection_name not in chroma_client.list_collections():
    chroma_client.create_collection(name=collection_name)
collection = chroma_client.get_collection(name=collection_name)

# Initialize the embeddings model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

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

# API endpoint to upload a PDF, extract text, and store it in PostgreSQL and ChromaDB
@app.post("/upload-pdf/")
async def upload_pdf(user_id: int, pdf_file: UploadFile = File(...)):
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(pdf_file)

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

    # Generate embeddings for the extracted text
    embeddings = embedding_model.encode([pdf_text])

    # Store the embeddings and document in ChromaDB
    collection.add(
        documents=[pdf_text],
        metadatas=[{"user_id": user_id, "doc_id": doc_id,"document":pdf_text}],
        embeddings=embeddings,
        ids=[str(doc_id)]  # Use doc_id as the identifier
    )

    return {"message": "PDF uploaded, content stored successfully.", "doc_id": doc_id}

# API endpoint to fetch document data by doc_id
@app.get("/fetch-document/{doc_id}")
async def fetch_document(doc_id: int):
    # Connect to the database
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Fetch document by doc_id
        cur.execute("SELECT user_id, document FROM document WHERE doc_id = %s", (doc_id,))
        result = cur.fetchone()

    conn.close()

    # Check if the document exists
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Unpack the result
    user_id, document_content = result
    return {
        "doc_id": doc_id,
        "user_id": user_id,
        "document": document_content
    }




def write_answer(question,references):
        prompt_reply = PromptTemplate.from_template(
            """
            #### question: 
            {question}
            ### references:
        {references}
        
        ### INSTRUCTION:
        you are very good reader and writer also. You need to write an short and clear answer for the question using the references.

        ##
        NO preamble.
        

            """
        )
        chain_email = prompt_reply | llm
        res = chain_email.invoke({"question": str(question), "references": references})
        return res.content


###chat model
@app.post("/chat/")
async def chat(user_id: int, question: str):
    # Generate embeddings for the question
    question_embedding = embedding_model.encode([question])

    # Perform a similarity search in ChromaDB for relevant document context
    results = collection.query(
        query_embeddings=question_embedding,
        n_results=3,  # Fetch top 3 similar results
        where={"user_id": user_id}
    ).get('metadatas', [])
    
    print(results)

    return write_answer(question,results)
    
    # Extract the most relevant document snippets
    # relevant_texts = [result["document"] for result in results["documents"]]
    # context = "\n".join(relevant_texts)

    # # Create a prompt for the LLM using the relevant document context
    # prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"

    # Use the LLM to generate a response based on the context
    # response = openai.Completion.create(
    #     engine="gpt-3.5-turbo",  # Choose appropriate model
    #     prompt=prompt,
    #     max_tokens=150,
    #     temperature=0.5,
    #     top_p=1.0,
    #     n=1,
    #     stop=None
    # )

    # answer = response.choices[0].text.strip()
    # return {"answer": answer}
     

    # return results