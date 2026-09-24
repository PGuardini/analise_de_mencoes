import os
import sys
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, select

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.models import Brand, Mention, Response


DATABASE_URL = 'sqlite:///mention_analytics.db'
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    """Function that create database and all registered tables"""
    SQLModel.metadata.create_all(engine)

def populate_database():
    BRANDS = ['Acme','Nimbus','Zenith']
    
    with Session(engine) as session:
        for brand in BRANDS:
            existing_brand = session.exec(select().where(Brand.name == brand)).first()
            if not existing_brand:
                new_brand = Brand(name=brand)
                session.add(new_brand)

        session.commit()

def get_session():
    with Session(engine) as session:
        yield session

if __name__ == '__main__':
    create_db_and_tables()
    populate_database()