import time
import pymysql
import os
import utils
from dotenv import load_dotenv
import logging


load_dotenv()

logger = logging.getLogger(__name__)

def get_db_connection():
    host = os.getenv("DB_HOST")
    db = os.getenv("DB_NAME")
    port = int(os.getenv("DB_PORT"))
    user = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")
    config = {
        "host": host,
        "database": db,
        "port": port,
        "user": user,
        "password": password,
        "autocommit": True,
        'cursorclass': pymysql.cursors.DictCursor
    }
    conn = pymysql.connect(**config)
    return conn

def get_knowledge_item_count(user_id: str):
    try:
        logger.info('Getting DB connection')
        connection = get_db_connection()
        cursor = connection.cursor()
        logger.info('Got DB connection')
    except Exception as err:
        raise err
    try:
        query = "SELECT COUNT(*) FROM document WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        logger.info(f"Knowledge item count: {result}")
        if result:
            return result['COUNT(*)']
        else:
            return 0  
    except Exception as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        connection.close()

MAX_RETRIES = 3
def insert_array_to_files_table(data):
    start_time = time.time()
    retries = 0
    while retries < MAX_RETRIES:  # Retry the query if there is a timeout error
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                columns_name = [
                    "user_id",
                    "file_id",
                    "file_name",
                    "content",
                    "deleted"
                ]
                table_name = "rag_db.document"
                columns = ", ".join(columns_name)
                values = ", ".join(["%s"] * len(columns_name))
                sql = (
                    f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
                )
                print(sql % data)
                cursor.execute(sql, data)
                conn.commit()
                end_time = time.time()
                elapsed_time = end_time - start_time
                logger.info(f"Chunks inserted into bot_indexes successfully, Time taken: {elapsed_time}")
                return
        except Exception as e:
            retries += 1
            logger.exception(f"Error occurred:{str(e)}, retrying for {retries} time...")
            conn.ping(reconnect=True)
        finally:
                if conn:
                    conn.close()  # Reconnect to the database
    logger.exception("Failed to execute query after multiple retries")
    raise Exception("Failed to execute query after multiple retries")

def get_bot_knowledge(user_id):
    try:
        logger.info('Getting DB connection')
        connection = get_db_connection()
        cursor = connection.cursor()
        logger.info('Got DB connection')
    except Exception as err:
        raise err
    try:
        query = "SELECT file_id, file_name, content FROM document WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        logger.info(f"Knowledge files: {result}")
        return result
    except Exception as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        connection.close()