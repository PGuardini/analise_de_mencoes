from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

class Response(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    origin_id: str | None = None
    question: str
    plataform: str
    model: str | None = None
    response_text: str
    date_hour: datetime
    sentiment: str | None = None

    # Response-Mention Relationship 1-N
    mentions: list['Mention'] = Relationship(back_populates='response')


class Brand(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    # Brand-Mention Relationship 1-N
    mentions: list['Mention'] = Relationship(back_populates='brand')


class Mention(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    # Mention-Response Relationship 1-1
    id_response: int | None = Field(default=None, foreign_key='response.id')
    response: Response | None = Relationship(back_populates='mentions')

    # Mention-Brand Relationship 1-1
    id_brand: int | None = Field(default=None, foreign_key='brand.id')
    brand: Brand | None = Relationship(back_populates='mentions')