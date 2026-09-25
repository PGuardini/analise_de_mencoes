from contextlib import asynccontextmanager
from fastapi import FastAPI , Depends
# from sqlmodel import Session, select
from data_manager.database import create_db_and_tables, populate_database
from app.models import Response, ResponseCreate
from app.services import ResponseService, get_response_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    populate_database()
    yield

app = FastAPI(lifespan=lifespan)

@app.get('/')
def root():
    return {'message':'hello world'}

@app.post('/responses', response_model=Response)
def create_responses(new_response: ResponseCreate, service: ResponseService = Depends(get_response_service)):
    return service.create_response(new_response)
