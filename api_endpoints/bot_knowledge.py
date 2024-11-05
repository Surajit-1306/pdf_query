from fastapi import HTTPException, Depends, File, UploadFile, APIRouter
from starlette.requests import Request
import os
import logging
import time
import db_utils
import utils
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/update_knowledge")
async def update_bot_knowledge_by_file(
    user_id: str,
    file: UploadFile = File(None)
):
    try:
        user_id = user_id.upper()
        logger.info(f"Processing update_bot_knowledge_by_file request for user_id: {user_id}")

        if file is None:
            raise HTTPException(status_code=400, detail="No file provided")
        else:
            utils.process_file(user_id,file)

        return {"message": "Knowledge Base updated successfully"}
    except Exception as e:
        logger.error(f"Error updating knowledge by file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating knowledge by file: {str(e)}")
    finally:
        logger.info("Finished processing update_bot_knowledge_by_file request.")


@router.get("/list_knowledge_files")
def get_bot_knowledge_files(user_id: str):
    try:
        user_id = user_id.upper()
        logger.info(f"Processing list_knowledge_files request for user_id: {user_id}")
        file_list = db_utils.get_bot_knowledge(user_id)
        logger.info({f"File knowledge source of bot_id {user_id}": file_list})
        return {"file_names": file_list}
    except Exception as e:
        logger.error(f"Error listing knowledge files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing knowledge files: {str(e)}")

