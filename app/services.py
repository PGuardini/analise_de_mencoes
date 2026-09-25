from fastapi import Depends, HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError

from data_manager.database import get_session
from data_manager.services import data_validation, data_cleansing, brand_mention_detector

from app.models import Brand, Mention, Response

class ResponseService:
    def __init__(self, session: Session):
        self.session = session
        self.brand_service = BrandService(self.session)
        self.mention_service = MentionService(self.session)

    def create_response(self, response):
        validated_data, validation_errors = data_validation(response)

        if not validated_data:
            raise HTTPException(status_code=400, detail={'errors':validation_errors})
        
        clean_data = data_cleansing(validated_data)

        if not clean_data:
            raise HTTPException(status_code=400, detail='No valid data to persist. Please review the format and resend the request.')

        successfull_responses = []
        
        for clean_response in clean_data:
            try:
                try:
                    new_response = Response.model_validate(clean_response)
                except ValidationError as e:
                    raise HTTPException(status_code=400, detail=e.errors())

                self.session.add(new_response)
                self.session.flush()

                detected_brands = brand_mention_detector(clean_response['response_text'])

                if detected_brands:
                    for brand_name in detected_brands:
                        actual_brand = self.brand_service.get_brand(brand_name)
                        if actual_brand:
                            self.mention_service.create_mention(new_response.id, actual_brand.id)

                self.session.commit()
                self.session.refresh(new_response)
                successfull_responses.append(new_response)
            except IntegrityError:
                self.session.rollback()

        if len(successfull_responses) == 1:
            return successfull_responses[0]
        else:
            return successfull_responses

            
        


class BrandService:
    def __init__(self, session: Session):
        self.session = session

    def get_brand(self, brand_name: str):
        brand = self.session.exec(select(Brand).where(Brand.name == brand_name)).first()
        return brand

class MentionService:
    def __init__(self, session: Session):
        self.session = session

    def create_mention(self, response_id: int, brand_id: int):
        try:
            new_mention = Mention(id_response=response_id, id_brand=brand_id)
            self.session.add(new_mention)
            return new_mention
        except Exception as e:
            raise HTTPException(status_code=422,
                                detail=f'Something went wrong.\n {e}')

    



def get_response_service(session: Session = Depends(get_session)):
    """Retrive a ResponseService Object to access Response data"""

    return ResponseService(session)