from contextlib import asynccontextmanager
from fastapi import FastAPI , Depends

from data_manager.database import create_db_and_tables, populate_database
from app.models import Response, ResponseCreate
from app.services import (ResponseService, get_response_service, 
                          BrandService, get_brand_service, 
                          MentionService, get_mention_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    populate_database()
    yield

app = FastAPI(lifespan=lifespan)

@app.get('/')
def root():
    return {
            'message':'Welcome to Brand mention analytics',
            'docs': 'The API documentation can be read in /docs'
            }

@app.post('/respostas', response_model=Response)
def create_responses(new_response: ResponseCreate, service: ResponseService = Depends(get_response_service)):
    return service.create_response(new_response)

@app.get('/share-of-voice')
def share_of_voice(marca: str, service: BrandService = Depends(get_brand_service)):
    return service.get_share_of_voice(marca)

@app.get('/top-citacoes')
def top_citations(n: int = 5, service: MentionService = Depends(get_mention_service)):
    return service.get_top_citations(n)