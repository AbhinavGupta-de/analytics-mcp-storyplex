"""Fandoms endpoints."""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func

from src.db.connection import get_session
from src.db.models import Fandom, Work, WorkFandom

router = APIRouter()


class FandomSummary(BaseModel):
    """Fandom summary."""

    id: int
    name: str
    category: Optional[str]
    work_count: int
    total_views: int
    total_likes: int


class FandomsResponse(BaseModel):
    """Paginated fandoms response."""

    fandoms: list[FandomSummary]
    total: int
    page: int
    page_size: int


@router.get("", response_model=FandomsResponse)
async def list_fandoms(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, le=200),
    search: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    sort_by: str = Query(default="works", regex="^(works|views|likes|name)$"),
):
    """List fandoms with statistics."""
    with get_session() as session:
        query = (
            session.query(
                Fandom.id,
                Fandom.name,
                Fandom.category,
                func.count(WorkFandom.work_id).label("work_count"),
                func.coalesce(func.sum(Work.latest_views), 0).label("total_views"),
                func.coalesce(func.sum(Work.latest_likes), 0).label("total_likes"),
            )
            .outerjoin(WorkFandom, Fandom.id == WorkFandom.fandom_id)
            .outerjoin(Work, WorkFandom.work_id == Work.id)
            .group_by(Fandom.id)
        )

        if search:
            query = query.filter(Fandom.name.ilike(f"%{search}%"))

        if category:
            query = query.filter(Fandom.category == category)

        # Get total before pagination
        total = query.count()

        # Apply sorting
        if sort_by == "views":
            query = query.order_by(func.sum(Work.latest_views).desc().nullslast())
        elif sort_by == "likes":
            query = query.order_by(func.sum(Work.latest_likes).desc().nullslast())
        elif sort_by == "name":
            query = query.order_by(Fandom.name)
        else:
            query = query.order_by(func.count(WorkFandom.work_id).desc())

        # Paginate
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        return FandomsResponse(
            fandoms=[
                FandomSummary(
                    id=r.id,
                    name=r.name,
                    category=r.category,
                    work_count=r.work_count,
                    total_views=r.total_views,
                    total_likes=r.total_likes,
                )
                for r in results
            ],
            total=total,
            page=page,
            page_size=page_size,
        )


@router.get("/categories")
async def list_fandom_categories():
    """Get list of fandom categories."""
    with get_session() as session:
        categories = (
            session.query(Fandom.category, func.count(Fandom.id).label("count"))
            .filter(Fandom.category.isnot(None))
            .group_by(Fandom.category)
            .order_by(func.count(Fandom.id).desc())
            .all()
        )

        return [{"category": c.category, "count": c.count} for c in categories]


@router.get("/{fandom_id}")
async def get_fandom(fandom_id: int):
    """Get fandom details with top works."""
    with get_session() as session:
        fandom = session.query(Fandom).filter(Fandom.id == fandom_id).first()

        if not fandom:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Fandom not found")

        # Get top works in this fandom
        top_works = (
            session.query(Work)
            .join(WorkFandom)
            .filter(WorkFandom.fandom_id == fandom_id)
            .order_by(Work.latest_views.desc())
            .limit(10)
            .all()
        )

        return {
            "id": fandom.id,
            "name": fandom.name,
            "category": fandom.category,
            "top_works": [
                {
                    "id": w.id,
                    "title": w.title,
                    "views": w.latest_views,
                    "likes": w.latest_likes,
                    "word_count": w.word_count,
                }
                for w in top_works
            ],
        }
