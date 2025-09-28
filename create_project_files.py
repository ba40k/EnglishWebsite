# create_project_files.py
import os
from pathlib import Path
BASE = Path(__file__).resolve().parent
APP = BASE / "app"
TEMPLATES = APP / "templates"
STATIC = APP / "static"

FILES = {
    "app/__init__.py": "",
    "app/models.py": r'''from sqlalchemy.orm import declarative_base, relationship
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
''',
    "app/schemas.py": r'''from pydantic import BaseModel
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
''',
    "app/crud.py": r'''from sqlalchemy.orm import Session
from . import models, schemas

def get_articles(db: Session, skip: int=0, limit: int=100):
    return db.query(models.Article).order_by(models.Article.created_at.desc()).offset(skip).limit(limit).all()

def get_article(db: Session, article_id: int):
    return db.query(models.Article).filter(models.Article.id==article_id).first()

def create_article(db: Session, article_in: schemas.ArticleCreate):
    article = models.Article(title=article_in.title, body=article_in.body, author=article_in.author)
    if article_in.collection_ids:
        cols = db.query(models.Collection).filter(models.Collection.id.in_(article_in.collection_ids)).all()
        article.collections = cols
    db.add(article)
    db.commit()
    db.refresh(article)
    return article

def add_comment(db: Session, article_id: int, comment_in: schemas.CommentCreate):
    comment = models.Comment(article_id=article_id, author=comment_in.author, text=comment_in.text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def get_collections(db: Session):
    return db.query(models.Collection).order_by(models.Collection.created_at.desc()).all()

def get_collection(db: Session, collection_id: int):
    return db.query(models.Collection).filter(models.Collection.id==collection_id).first()

def create_collection(db: Session, collection_in: schemas.CollectionCreate):
    col = models.Collection(title=collection_in.title, description=collection_in.description)
    db.add(col)
    db.commit()
    db.refresh(col)
    return col

def get_tests(db: Session):
    return db.query(models.Test).order_by(models.Test.created_at.desc()).all()

def get_test(db: Session, test_id: int):
    return db.query(models.Test).filter(models.Test.id==test_id).first()

def create_test(db: Session, test_in: schemas.TestCreate):
    t = models.Test(title=test_in.title, description=test_in.description)
    db.add(t)
    db.flush()
    for q in test_in.questions:
        qdb = models.Question(test_id=t.id, text=q.text, choices="|".join(q.choices), correct_index=q.correct_index)
        db.add(qdb)
    db.commit()
    db.refresh(t)
    return t
''',
    "app/main.py": r'''from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import json

from . import models, crud, schemas

BASE_DIR = Path(__file__).resolve().parent
DB_URL = f"sqlite:///{str(BASE_DIR / 'database.db')}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False}, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db=Depends(get_db)):
    articles = crud.get_articles(db, limit=10)
    collections = crud.get_collections(db)
    tests = crud.get_tests(db)
    return templates.TemplateResponse("index.html", {"request": request, "articles": articles, "collections": collections, "tests": tests})

@app.get("/articles", response_class=HTMLResponse)
def articles_list(request: Request, db=Depends(get_db)):
    articles = crud.get_articles(db)
    return templates.TemplateResponse("articles.html", {"request": request, "articles": articles})

@app.get("/articles/create", response_class=HTMLResponse)
def create_article_form(request: Request, db=Depends(get_db)):
    collections = crud.get_collections(db)
    return templates.TemplateResponse("create_article.html", {"request": request, "collections": collections})

@app.post("/articles/create")
def create_article(title: str = Form(...), body: str = Form(...), author: str = Form("Anonymous"), collection_ids: str = Form(""), db=Depends(get_db)):
    ids = [int(x) for x in collection_ids.split(",") if x.strip().isdigit()]
    article_in = schemas.ArticleCreate(title=title, body=body, author=author, collection_ids=ids)
    article = crud.create_article(db, article_in)
    return RedirectResponse(url=f"/articles/{article.id}", status_code=303)

@app.get("/articles/{article_id}", response_class=HTMLResponse)
def article_detail(request: Request, article_id: int, db=Depends(get_db)):
    article = crud.get_article(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return templates.TemplateResponse("article_detail.html", {"request": request, "article": article})

@app.post("/articles/{article_id}/comments")
def add_comment(article_id: int, author: str = Form("Anonymous"), text: str = Form(...), db=Depends(get_db)):
    comment_in = schemas.CommentCreate(author=author, text=text)
    _ = crud.add_comment(db, article_id, comment_in)
    return RedirectResponse(url=f"/articles/{article_id}", status_code=303)

@app.get("/collections", response_class=HTMLResponse)
def collections_list(request: Request, db=Depends(get_db)):
    collections = crud.get_collections(db)
    return templates.TemplateResponse("collections.html", {"request": request, "collections": collections})

@app.get("/collections/create", response_class=HTMLResponse)
def create_collection_form(request: Request):
    return templates.TemplateResponse("create_collection.html", {"request": request})

@app.post("/collections/create")
def create_collection(title: str = Form(...), description: str = Form(""), db=Depends(get_db)):
    col_in = schemas.CollectionCreate(title=title, description=description)
    col = crud.create_collection(db, col_in)
    return RedirectResponse(url=f"/collections/{col.id}", status_code=303)

@app.get("/collections/{collection_id}", response_class=HTMLResponse)
def collection_detail(request: Request, collection_id: int, db=Depends(get_db)):
    col = crud.get_collection(db, collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    return templates.TemplateResponse("collection_detail.html", {"request": request, "collection": col})

@app.get("/tests", response_class=HTMLResponse)
def tests_list(request: Request, db=Depends(get_db)):
    tests = crud.get_tests(db)
    return templates.TemplateResponse("tests.html", {"request": request, "tests": tests})

@app.get("/tests/create", response_class=HTMLResponse)
def create_test_form(request: Request):
    return templates.TemplateResponse("create_test.html", {"request": request})

@app.post("/tests/create")
def create_test_simple(title: str = Form(...), description: str = Form(""), questions_json: str = Form(""), db=Depends(get_db)):
    try:
        questions = json.loads(questions_json or "[]")
    except Exception:
        raise HTTPException(status_code=400, detail="questions_json must be valid JSON")
    q_objs = []
    for q in questions:
        q_objs.append(schemas.QuestionCreate(text=q["text"], choices=q["choices"], correct_index=int(q["correct_index"])))
    test_in = schemas.TestCreate(title=title, description=description, questions=q_objs)
    test = crud.create_test(db, test_in)
    return RedirectResponse(url=f"/tests/{test.id}", status_code=303)

@app.get("/tests/{test_id}", response_class=HTMLResponse)
def test_detail(request: Request, test_id: int, db=Depends(get_db)):
    test = crud.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    qlist = []
    for q in test.questions:
        qlist.append({"id": q.id, "text": q.text, "choices": q.choices.split("|")})
    return templates.TemplateResponse("test_detail.html", {"request": request, "test": test, "questions": qlist})

@app.post("/tests/{test_id}/submit")
def submit_test(test_id: int, answers: str = Form(...), db=Depends(get_db)):
    try:
        ans = json.loads(answers)
    except Exception:
        raise HTTPException(status_code=400, detail="answers must be valid JSON")
    test = crud.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    total = len(test.questions)
    correct = 0
    for q in test.questions:
        sel = ans.get(str(q.id))
        if sel is None:
            continue
        if int(sel) == q.correct_index:
            correct += 1
    score = {"total": total, "correct": correct}
    return templates.TemplateResponse("test_result.html", {"request": request, "score": score, "test": test})
''',
    "app/templates/base.html": r'''<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Mini CMS</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header>
    <h1><a href="/">Mini CMS</a></h1>
    <nav>
      <a href="/articles">Статьи</a> |
      <a href="/collections">Подборки</a> |
      <a href="/tests">Тесты</a>
    </nav>
  </header>
  <main>
    {% block content %}{% endblock %}
  </main>
  <footer>
    <small>Минимальный пример на FastAPI</small>
  </footer>
</body>
</html>
''',
    "app/templates/index.html": r'''{% extends "base.html" %}
{% block content %}
<h2>Последние статьи</h2>
<ul>
  {% for a in articles %}
    <li><a href="/articles/{{ a.id }}">{{ a.title }}</a> — {{ a.author }}</li>
  {% else %}
    <li>Нет статей</li>
  {% endfor %}
</ul>

<h2>Подборки</h2>
<ul>
  {% for c in collections %}
    <li><a href="/collections/{{ c.id }}">{{ c.title }}</a></li>
  {% else %}
    <li>Нет подборок</li>
  {% endfor %}
</ul>

<h2>Тесты</h2>
<ul>
  {% for t in tests %}
    <li><a href="/tests/{{ t.id }}">{{ t.title }}</a></li>
  {% else %}
    <li>Нет тестов</li>
  {% endfor %}
</ul>
{% endblock %}''',
    "app/templates/articles.html": r'''{% extends "base.html" %}
{% block content %}
<h2>Статьи</h2>
<a href="/articles/create">Создать статью</a>
<ul>
  {% for a in articles %}
    <li><a href="/articles/{{ a.id }}">{{ a.title }}</a> — {{ a.author }}</li>
  {% else %}
    <li>Нет статей</li>
  {% endfor %}
</ul>
{% endblock %}''',
    "app/templates/create_article.html": r'''{% extends "base.html" %}
{% block content %}
<h2>Создать статью</h2>
<form action="/articles/create" method="post">
  <label>Заголовок</label><br>
  <input name="title" required><br>
  <label>Текст</label><br>
  <textarea name="body" rows="8" required></textarea><br>
  <label>Автор</label><br>
  <input name="author"><br>
  <label>ID подборок (через запятую)</label><br>
  <input name="collection_ids" placeholder="1,2"><br>
  <button type="submit">Создать</button>
</form>
{% endblock %}''',
    "app/templates/article_detail.html": r'''{% extends "base.html" %}
{% block content %}
<article>
  <h2>{{ article.title }}</h2>
  <p><small>Автор: {{ article.author }} | {{ article.created_at }}</small></p>
  <div>{{ article.body | safe }}</div>

  <section>
    <h3>Комментарии</h3>
    <ul>
      {% for c in article.comments %}
        <li><strong>{{ c.author }}</strong>: {{ c.text }} <small>{{ c.created_at }}</small></li>
      {% else %}
        <li>Пока нет комментариев</li>
      {% endfor %}
    </ul>

    <h4>Оставить комментарий</h4>
    <form action="/articles/{{ article.id }}/comments" method="post">
      <input type="text" name="author" placeholder="Ваше имя">
      <br>
      <textarea name="text" required placeholder="Текст комментария"></textarea>
      <br>
      <button type="submit">Отправить</button>
    </form>
  </section>
</article>
{% endblock %}''',
    "app/templates/collections.html": r'''{% extends "base.html" %}
{% block content %}
<h2>Подборки</h2>
<a href="/collections/create">Создать подборку</a>
<ul>
  {% for c in collections %}
    <li><a href="/collections/{{ c.id }}">{{ c.title }}</a> — {{ c.created_at }}</li>
  {% else %}
    <li>Нет подборок</li>
  {% endfor %}
</ul>
{% endblock %}''',
    "app/templates/create_collection.html": r'''{% extends "base.html" %}
{% block content %}
<h2>Создать подборку</h2>
<form action="/collections/create" method="post">
  <label>Название</label><br>
  <input name="title" required><br>
  <label>Описание</label><br>
  <textarea name="description" rows="4"></textarea><br>
  <button type="submit">Создать</button>
</form>
{% endblock %}''',
    "app/templates/collection_detail.html": r'''{% extends "base.html" %}
{% block content %}
<h2>{{ collection.title }}</h2>
<p>{{ collection.description }}</p>

<h3>Статьи в подборке</h3>
<ul>
  {% for a in collection.articles %}
    <li><a href="/articles/{{ a.id }}">{{ a.title }}</a></li>
  {% else %}
    <li>Нет статей в подборке</li>
  {% endfor %}
</ul>
{% endblock %}''',
    "app/templates/tests.html": r'''{% extends "base.html" %}
{% block content %}
<h2>Тесты</h2>
<a href="/tests/create">Создать тест</a>
<ul>
  {% for t in tests %}
    <li><a href="/tests/{{ t.id }}">{{ t.title }}</a></li>
  {% else %}
    <li>Нет тестов</li>
  {% endfor %}
</ul>
{% endblock %}''',
    "app/templates/create_test.html": r'''{% extends "base.html" %}
{% block content %}
<h2>Создать тест</h2>
<form action="/tests/create" method="post">
  <label>Название</label><br>
  <input name="title" required><br>
  <label>Описание</label><br>
  <input name="description"><br>
  <label>Questions JSON</label><br>
  <textarea name="questions_json" rows="10" placeholder='[{"text":"Q1","choices":["A","B"],"correct_index":0}]'></textarea><br>
  <small>questions_json — JSON-массив вопросов с полями text, choices и correct_index</small><br>
  <button type="submit">Создать</button>
</form>
{% endblock %}''',
    "app/templates/test_detail.html": r'''{% extends "base.html" %}
{% block content %}
<h2>{{ test.title }}</h2>
<p>{{ test.description }}</p>
<form action="/tests/{{ test.id }}/submit" method="post" id="testform">
  {% for q in questions %}
    <div>
      <p><strong>{{ loop.index }}. {{ q.text }}</strong></p>
      {% for choice in q.choices %}
        <label>
          <input type="radio" name="q{{ q.id }}" value="{{ loop.index0 }}"> {{ choice }}
        </label><br>
      {% endfor %}
    </div>
  {% endfor %}
  <input type="hidden" name="answers" id="answers">
  <button type="button" onclick="submitAnswers()">Отправить</button>
</form>

<script>
function submitAnswers(){
  const data = {};
  {% for q in questions %}
    const els = document.getElementsByName('q{{ q.id }}');
    let sel = null;
    for(let i=0;i<els.length;i++){ if(els[i].checked){ sel = els[i].value; break; } }
    if(sel !== null) data['{{ q.id }}'] = parseInt(sel);
  {% endfor %}
  document.getElementById('answers').value = JSON.stringify(data);
  document.getElementById('testform').submit();
}
</script>
{% endblock %}''',
    "app/templates/test_result.html": r'''{% extends "base.html" %}
{% block content %}
<h2>Результат: {{ score.correct }} / {{ score.total }}</h2>
<a href="/tests">К списку тестов</a>
{% endblock %}''',
    "app/static/style.css": r'''body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 1rem; color:#222; }
header { border-bottom:1px solid #ddd; padding-bottom:10px; margin-bottom:20px; }
nav a { margin-right:10px; color:#0366d6; text-decoration:none; }
main { margin-top:20px; }
form input, form textarea { width: 100%; padding:8px; margin:6px 0; box-sizing:border-box; }
button { padding:8px 12px; background:#0366d6; color:#fff; border:none; cursor:pointer; }
footer { margin-top:40px; color:#666; font-size:0.9rem; border-top:1px solid #eee; padding-top:10px;}'''
}

def ensure_dirs():
    APP.mkdir(exist_ok=True)
    TEMPLATES.mkdir(parents=True, exist_ok=True)
    STATIC.mkdir(parents=True, exist_ok=True)

def write_files():
    for rel, content in FILES.items():
        p = BASE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
    print("Created files under:", APP)

if __name__ == "__main__":
    ensure_dirs()
    write_files()
    print("Done. Now run:")
    print("  pip install -r requirements.txt")
    print("  uvicorn app.main:app --reload")
