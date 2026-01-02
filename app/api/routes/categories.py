from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryOut
from app.services.catalog_service import create_category

router = APIRouter(prefix="/categories")

@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.id.asc()).all()

@router.post("", response_model=CategoryOut, status_code=201)
def create(payload: CategoryCreate, db: Session = Depends(get_db)):
    exists = db.query(Category).filter(Category.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Category exists")
    return create_category(db, payload.name)
