from pydantic import BaseModel
from typing import List, Optional

class CommentCreate(BaseModel):
    author: Optional[str] = "Anonymous"
    text: str

class ArticleCreate(BaseModel):
    title: str
    body: str
    author: Optional[str] = "Anonymous"
    collection_ids: Optional[List[int]] = []

class CollectionCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class QuestionCreate(BaseModel):
    text: str
    choices: List[str]
    correct_index: int

class TestCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    questions: List[QuestionCreate] = []
