import os
import time
import tempfile
import logging
import db_utils
import uuid
import chroma_utils
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

def process_file(user_id, file):
    try:
        logger.info(f"Processing file for user: {user_id}")
        fileType, doc, file_size, characters = extract_text(file)
        docs = split_docs([doc])
        file_id = generate_knowledge_id(user_id)
        index_obj = chroma_utils.Knowledgebase_index_chromadb()
        index_obj.insert_knowledge(user_id=user_id, index_id=file_id, docs=docs, source=file.filename, source_type='file')
    except Exception as e:
        logger.error(f"An error occurred while processing the file for user {user_id}: {e}")


def extract_text(file):
    fileType = None
    doc = None
    file_size = None
    characters = 0
    try:
        logger.info(f'Inside extract_text')
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write the contents of the uploaded file to the temporary file
            temp_file.write(file.file.read())
            temp_file_path = temp_file.name
            logger.info(f"Temp file path: {temp_file_path}")
            file_size = round(os.path.getsize(temp_file_path) / 10**6, 2)
            logger.info(f"File_size: {file_size} MB")
            fileType = file.content_type
            content = ""
            characters = 0
            if fileType == "application/pdf":
                elements = partition_pdf(temp_file_path, strategy="fast")
                for element in elements:
                    content += str(element)
                    characters += len(str(element))
            elif fileType == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                elements = partition_docx(temp_file_path)
                for element in elements:
                    content += str(element)
                    characters += len(str(element))
            elif fileType == "text/plain":
                print("Text")
                with open(temp_file_path, 'r') as f:
                    content = f.read()
            
            metadata = {"file": fileType}
            if type(content) != list:
                characters = len(content)
                doc = Document(page_content=content, metadata=metadata)
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    except Exception as e:
        logger.error(f"An error occurred in extract_text: {e}")
    finally:
        return fileType, doc, file_size, characters
    

def split_docs(documents, chunk_size=1200, chunk_overlap=400):
    start_time = time.time()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents(documents)
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Time taken to split/chunking documents: {elapsed_time:.2f} seconds")
    logger.info(f"Number of chunks: {len(docs)}")
    return docs

def generate_knowledge_id(user_id: str):
    try:
        knowledg_item_count = db_utils.get_knowledge_item_count(user_id)
        logger.info(f"Knowledge item count for user {user_id}: {knowledg_item_count} and type: {type(knowledg_item_count)}")
        knowledg_item_count += 1
        base_uuid = uuid.uuid4()
        prefix = f"{user_id}"
        knowledge_id = f"{prefix}_{knowledg_item_count}_{base_uuid.hex[:3]}"
        return knowledge_id
    except Exception as e:
        logger.error(f"An error occurred while generating knowledge ID for user {user_id}: {e}")
        return None

