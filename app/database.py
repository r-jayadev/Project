"""
Database Configuration Module

This module creates SQLalchemy and declarative base that will be used throughout.
"""
from app.config import settings 

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi import HTTPException

#Connect to Postgres using config.py
DATABASE_URL=(
    f"postgresql://{settings.POSTGRES_USER}:"
    f"{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/"
    f"{settings.POSTGRES_DB}"
)

#Create the SQLalchemy engine - manages communication with Postgres
engine = create_engine(DATABASE_URL, echo=True)

#Create a session factory - each api call will create its own session 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base class for all SQLAlchemy Models
Base=declarative_base()

def get_db():
    """
    Dependency function

    Creates a new database session for evry request and closes it automatically.
    """
    db=SessionLocal()

    try:
        yield db

    finally:
        db.close()
