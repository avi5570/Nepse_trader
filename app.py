import os

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@db:5432/nepse"
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class MessageCounter(Base):
    __tablename__ = "message_counter"

    id = Column(Integer, primary_key=True, index=True)
    count = Column(Integer, nullable=False, default=0)
    title = Column(String(128), nullable=False, default="Nepse Trader Backend")
    text = Column(String(256), nullable=False, default="Hello from Python FastAPI backend!")


class MessageResponse(BaseModel):
    title: str
    text: str
    count: int


app = FastAPI(title="Nepse Trader API")

origins = [
    "http://localhost:4200"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        row = db.execute(select(MessageCounter)).scalars().first()
        if row is None:
            db.add(MessageCounter(count=0))
            db.commit()


@app.on_event("startup")
def startup_event():
    try:
        ensure_database()
    except SQLAlchemyError:
        pass


@app.get("/api/message", response_model=MessageResponse)
def get_message(db: Session = Depends(get_db)):
    counter = db.execute(select(MessageCounter)).scalars().first()
    if counter is None:
        counter = MessageCounter(count=0)
        db.add(counter)

    counter.count += 1
    db.commit()
    db.refresh(counter)

    return {
        "title": counter.title,
        "text": counter.text,
        "count": counter.count,
    }
