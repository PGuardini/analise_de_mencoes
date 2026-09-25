from typing import Optional
from datetime import datetime
from pydantic import NaiveDatetime
from sqlmodel import SQLModel, Field, Relationship

class Response(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    origin_id: str | None = Field(unique=True)
    question: str
    platform: str
    model: str | None = None
    response_text: str
    date_hour: NaiveDatetime | None = Field(default_factory=datetime.now)
    sentiment: str | None = None

    # Response-Mention Relationship 1-N
    mentions: list['Mention'] = Relationship(back_populates='response')

class ResponseCreate(SQLModel):
    id: str
    pergunta: str
    plataforma: str
    modelo: Optional[str] = None
    resposta_texto: str
    data_hora: Optional[str] = None
    sentimento: Optional[str] = None


class Brand(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    # Brand-Mention Relationship 1-N
    mentions: list['Mention'] = Relationship(back_populates='brand')


class Mention(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    brand_ocurrence_count: int

    # Mention-Response Relationship 1-1
    id_response: int | None = Field(default=None, foreign_key='response.id')
    response: Response | None = Relationship(back_populates='mentions')

    # Mention-Brand Relationship 1-1
    id_brand: int | None = Field(default=None, foreign_key='brand.id')
    brand: Brand | None = Relationship(back_populates='mentions')