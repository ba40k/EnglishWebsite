from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import json

from . import models, crud, schemas, ai_helper

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
    # Generate AI summary and vocabulary
    ai_content = ai_helper.generate_article_summary(article.title, article.body)
    return templates.TemplateResponse("article_detail.html", {
        "request": request, 
        "article": article, 
        "ai_summary": ai_content.get("summary", ""),
        "ai_vocabulary": ai_content.get("vocabulary", [])
    })

@app.post("/articles/{article_id}/ask-ai")
def ask_ai_about_article(article_id: int, question: str = Form(...), db=Depends(get_db)):
    """Ask AI a question about an article."""
    article = crud.get_article(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Ask AI the question
    answer = ai_helper.ask_about_article(article.title, article.body, question)
    
    return {"answer": answer}

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
async def submit_test(request: Request, test_id: int, answers: str = Form(...), db=Depends(get_db)):
    try:
        ans = json.loads(answers)
    except Exception:
        raise HTTPException(status_code=400, detail="answers must be valid JSON")
    test = crud.get_test(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    total = len(test.questions)
    correct = 0
    results = []
    
    for q in test.questions:
        sel = ans.get(str(q.id))
        is_correct = False
        if sel is not None and int(sel) == q.correct_index:
            correct += 1
            is_correct = True
        
        choices_list = q.choices.split("|")
        results.append({
            "question": q.text,
            "correct_answer": choices_list[q.correct_index] if q.correct_index < len(choices_list) else "N/A",
            "user_answer": choices_list[int(sel)] if sel is not None and int(sel) < len(choices_list) else "Not answered",
            "is_correct": is_correct
        })
    
    # Generate AI explanations
    ai_explanations = ai_helper.explain_test_answers(test.title, results)
    
    score = {"total": total, "correct": correct}
    return templates.TemplateResponse("test_result.html", {
        "request": request, 
        "score": score, 
        "test": test,
        "results": results,
        "ai_explanations": ai_explanations
    })
