import time
from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv
import logging

import db_utils
load_dotenv()


logger = logging.getLogger(__name__)

class Knowledgebase_index_chromadb:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path="chromadb_rag")
            self.collection = self.client.get_or_create_collection("rag_index")
            self.model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")
            self.num = self.collection.count()
            logger.info("Initialization successful for ChromaDB knowledge base")
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}")
            raise e
        finally:
            logger.info("Initialization complete")

    def insert_knowledge(self, user_id, index_id, docs, source, source_type='file'):
        try:
            start_time = time.time()
            key = self.num
            ids = []
            embeddings = []
            metadatas = []
            logger.info(f"Starting knowledge insertion for user_id: {user_id}, source: {source}")
            for doc in docs:
                if source_type == 'file':
                    page_content = doc.page_content

                metadata = {
                    "knowledge": page_content,
                    "project": "rag_pdf",
                    "model": "multi-qa-MiniLM-L6-cos-v1",
                    "approach": "user_" + user_id,
                    "index": index_id,
                    "source": source,
                }
                if source_type == 'file':
                    metadata['source_type'] = "file"

                ids.append("user_" + str(key))
                metadatas.append(metadata)
                embeddings.append(self.model.encode(page_content).tolist())
                key += 1
                self.collection.upsert(
                    ids=ids, embeddings=embeddings, metadatas=metadatas
                )
                ids = []
                embeddings = []
                metadatas = []
            
            context = ""
            for i in range(len(docs)):
                context += str(docs[i].page_content) + "\n"

            sql_data = (user_id, index_id, source, context, False)
            logger.info({"SOURCES": source})
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(f"Insertion into ChromaDB knowledge Base from {source} successful, Time taken: {elapsed_time}")
            db_utils.insert_array_to_files_table(data=sql_data)
        
        except Exception as e:
            logger.error(f"Error during insertion of knowledge for bot_id {user_id} from source {source}: {str(e)}")
            raise e