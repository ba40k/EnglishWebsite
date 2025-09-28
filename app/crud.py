from sqlalchemy.orm import Session
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
