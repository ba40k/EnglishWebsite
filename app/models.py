from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey, DateTime
from datetime import datetime

Base = declarative_base()

article_collection = Table(
    "article_collection",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("collection_id", Integer, ForeignKey("collections.id"), primary_key=True),
)

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    author = Column(String(100), default="Anonymous")
    created_at = Column(DateTime, default=datetime.utcnow)

    comments = relationship("Comment", back_populates="article", cascade="all, delete-orphan")
    collections = relationship("Collection", secondary=article_collection, back_populates="articles")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    author = Column(String(100), default="Anonymous")
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="comments")

class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    articles = relationship("Article", secondary=article_collection, back_populates="collections")

class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    text = Column(Text, nullable=False)
    choices = Column(Text, nullable=False)
    correct_index = Column(Integer, nullable=False)

    test = relationship("Test", back_populates="questions")
