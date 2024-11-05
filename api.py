import logging
import time
from dotenv import load_dotenv
import os
load_dotenv(override=True)

logging.basicConfig(filename='api.log', filemode='a', level=logging.INFO, \
                    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(lineno)d- %(message)s')
logger = logging.getLogger(__name__)
from api_endpoints import bot_knowledge, chat
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware


app = FastAPI()

@app.middleware("http")
async def log_response_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Request: {request.url.path} completed in {process_time:.4f} seconds")
    return response 
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.include_router(bot_knowledge.router, tags=["Bot Knowledge"])
#app.include_router(chat.router, tags=["Chat"])