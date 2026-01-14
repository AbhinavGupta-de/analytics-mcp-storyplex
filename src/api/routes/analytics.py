"""Analytics endpoints for dashboard statistics."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func

from src.db.connection import get_session
from src.db.models import Author, EngagementSnapshot, Fandom, Platform, Tag, Work, WorkFandom

router = APIRouter()


class SummaryStats(BaseModel):
    """Overall summary statistics."""

    total_works: int
    total_authors: int
    total_fandoms: int
    total_tags: int
    total_words: int
    total_views: int
    total_likes: int
    platforms: list[dict]


class TimeSeriesPoint(BaseModel):
    """Single point in time series data."""

    date: str
    value: int


class FandomStats(BaseModel):
    """Fandom statistics."""

    name: str
    work_count: int
    total_views: int
    total_likes: int
    avg_word_count: float


class TagStats(BaseModel):
    """Tag statistics."""

    name: str
    category: Optional[str]
    work_count: int


@router.get("/summary", response_model=SummaryStats)
async def get_summary_stats():
    """Get overall summary statistics for the dashboard."""
    with get_session() as session:
        work_count = session.query(func.count(Work.id)).scalar() or 0
        author_count = session.query(func.count(Author.id)).scalar() or 0
        fandom_count = session.query(func.count(Fandom.id)).scalar() or 0
        tag_count = session.query(func.count(Tag.id)).scalar() or 0
        total_words = session.query(func.sum(Work.word_count)).scalar() or 0
        total_views = session.query(func.sum(Work.latest_views)).scalar() or 0
        total_likes = session.query(func.sum(Work.latest_likes)).scalar() or 0

        # Platform breakdown
        platforms = (
            session.query(
                Platform.name,
                func.count(Work.id).label("work_count"),
            )
            .outerjoin(Work)
            .group_by(Platform.id)
            .all()
        )

        return SummaryStats(
            total_works=work_count,
            total_authors=author_count,
            total_fandoms=fandom_count,
            total_tags=tag_count,
            total_words=total_words,
            total_views=total_views,
            total_likes=total_likes,
            platforms=[{"name": p.name, "work_count": p.work_count} for p in platforms],
        )


@router.get("/top-fandoms", response_model=list[FandomStats])
async def get_top_fandoms(
    limit: int = Query(default=20, le=100),
    sort_by: str = Query(default="works", regex="^(works|views|likes)$"),
):
    """Get top fandoms by various metrics."""
    with get_session() as session:
        query = (
            session.query(
                Fandom.name,
                func.count(WorkFandom.work_id).label("work_count"),
                func.coalesce(func.sum(Work.latest_views), 0).label("total_views"),
                func.coalesce(func.sum(Work.latest_likes), 0).label("total_likes"),
                func.coalesce(func.avg(Work.word_count), 0).label("avg_word_count"),
            )
            .join(WorkFandom, Fandom.id == WorkFandom.fandom_id)
            .join(Work, WorkFandom.work_id == Work.id)
            .group_by(Fandom.id)
        )

        if sort_by == "views":
            query = query.order_by(func.sum(Work.latest_views).desc())
        elif sort_by == "likes":
            query = query.order_by(func.sum(Work.latest_likes).desc())
        else:
            query = query.order_by(func.count(WorkFandom.work_id).desc())

        results = query.limit(limit).all()

        return [
            FandomStats(
                name=r.name,
                work_count=r.work_count,
                total_views=r.total_views,
                total_likes=r.total_likes,
                avg_word_count=round(r.avg_word_count, 0),
            )
            for r in results
        ]


@router.get("/top-tags", response_model=list[TagStats])
async def get_top_tags(
    limit: int = Query(default=30, le=100),
    category: Optional[str] = Query(default=None),
):
    """Get most used tags."""
    from src.db.models import WorkTag

    with get_session() as session:
        query = (
            session.query(
                Tag.name,
                Tag.category,
                func.count(WorkTag.work_id).label("work_count"),
            )
            .join(WorkTag, Tag.id == WorkTag.tag_id)
            .group_by(Tag.id)
        )

        if category:
            query = query.filter(Tag.category == category)

        results = query.order_by(func.count(WorkTag.work_id).desc()).limit(limit).all()

        return [
            TagStats(name=r.name, category=r.category, work_count=r.work_count) for r in results
        ]


@router.get("/engagement-trends")
async def get_engagement_trends(
    days: int = Query(default=30, le=90),
):
    """Get engagement trends over time."""
    with get_session() as session:
        since = datetime.utcnow() - timedelta(days=days)

        # Get daily aggregated snapshots
        results = (
            session.query(
                func.date(EngagementSnapshot.snapshot_date).label("date"),
                func.sum(EngagementSnapshot.views).label("views"),
                func.sum(EngagementSnapshot.likes).label("likes"),
                func.count(EngagementSnapshot.id).label("snapshots"),
            )
            .filter(EngagementSnapshot.snapshot_date >= since)
            .group_by(func.date(EngagementSnapshot.snapshot_date))
            .order_by(func.date(EngagementSnapshot.snapshot_date))
            .all()
        )

        return {
            "views": [{"date": str(r.date), "value": r.views or 0} for r in results],
            "likes": [{"date": str(r.date), "value": r.likes or 0} for r in results],
        }


@router.get("/word-count-distribution")
async def get_word_count_distribution():
    """Get distribution of works by word count ranges."""
    with get_session() as session:
        # Define ranges
        ranges = [
            (0, 1000, "< 1K"),
            (1000, 5000, "1K-5K"),
            (5000, 10000, "5K-10K"),
            (10000, 50000, "10K-50K"),
            (50000, 100000, "50K-100K"),
            (100000, 500000, "100K-500K"),
            (500000, float("inf"), "> 500K"),
        ]

        distribution = []
        for min_wc, max_wc, label in ranges:
            query = session.query(func.count(Work.id)).filter(Work.word_count >= min_wc)
            if max_wc != float("inf"):
                query = query.filter(Work.word_count < max_wc)
            count = query.scalar() or 0
            distribution.append({"range": label, "count": count})

        return distribution
