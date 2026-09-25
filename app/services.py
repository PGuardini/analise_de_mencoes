from fastapi import Depends, HTTPException
from sqlmodel import Session, select, func
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
                    for brand_name, brand_ocurrency_count in detected_brands.items():
                        actual_brand = self.brand_service.get_brand(brand_name)
                        
                        if actual_brand:
                            self.mention_service.create_mention(
                                                                new_response.id, 
                                                                actual_brand.id,
                                                                brand_ocurrency_count
                                                            )

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

    def get_share_of_voice(self, brand: str):
        brand_exists = self.get_brand(brand.capitalize())
        if not brand_exists:
            raise HTTPException(status_code=404, detail='Could not find this brand. Please try a new one.')

        # Percentual total de marca nas respostas
        total_response = self.session.exec(select(func.count()).select_from(Response)).one()
        brand_statement = select(func.count()).select_from(Mention).where(Mention.id_brand == brand_exists.id)
        total_brand_in_responses = self.session.exec(brand_statement).one()

        total_percent_by_brand = (total_brand_in_responses * 100) / total_response

        # Percentual de marca por plataforma
        platform_statement = select(Response.platform, func.count()).group_by(Response.platform)
        total_by_platform = dict(self.session.exec(platform_statement).all())

        brand_by_platform_statement = (select(Response.platform, func.count())
                                        .select_from(Mention)
                                        .join(Response, Mention.id_response == Response.id)
                                        .where(Mention.id_brand == brand_exists.id)
                                        .group_by(Response.platform))

        brand_by_platform = dict(self.session.exec(brand_by_platform_statement).all())

        total_percent_brand_by_platform = {}
        for platform, count in brand_by_platform.items():
            total_percent_brand_by_platform[platform] = (count * 100) / total_by_platform[platform]

        share_of_voice = {
            'percentual_marca_em_respostas': total_percent_by_brand,
            'percentual_marca_por_plataforma': total_percent_brand_by_platform
        }
        return share_of_voice


class MentionService:
    def __init__(self, session: Session):
        self.session = session

    def create_mention(self, response_id: int, brand_id: int, brand_ocurrency_count: int):
        try:
            new_mention = Mention(id_response = response_id, 
                                  id_brand = brand_id,
                                  brand_ocurrency_count=brand_ocurrency_count)

            self.session.add(new_mention)
            return new_mention
        except Exception as e:
            raise HTTPException(status_code=422,
                                detail=f'Something went wrong.\n {e}')

    def get_top_citations(self, n: int = 5):
        citation_statement = (
                                select(
                                     Mention.id_response,
                                     func.count(func.distinct(Mention.id_brand)).label('distinct_brands'),
                                     func.sum(Mention.brand_ocurrency_count).label('total_ocurrences')
                                    )
                                    .group_by(Mention.id_response)
                                    .order_by(
                                              func.count(func.distinct(Mention.id_brand)).desc(),
                                              func.sum(Mention.brand_ocurrency_count).desc()
                                            )
                                    .limit(n)
                             )
        
        ranking = self.session.exec(citation_statement).all()

        top_citations = []
        for response_id, distinct_brands, total_ocurrences in ranking:
            response = self.session.get(Response, response_id)
            top_citations.append({
                'plataforma': response.platform,
                'modelo': response.model,
                'resposta_texto': response.response_text,
                'marcas_distintas_citadas': distinct_brands,
                'total_de_ocorrencias': total_ocurrences
            })

        return top_citations

def get_response_service(session: Session = Depends(get_session)):
    """Retrieve a ResponseService Object to access Response data"""

    return ResponseService(session)

def get_brand_service(session: Session = Depends(get_session)):
    """Retrieve a BrandService Object to access Brand data"""

    return BrandService(session)

def get_mention_service(session: Session = Depends(get_session)):
    """Retrieve a MentionService Object to access Mention data"""

    return MentionService(session)