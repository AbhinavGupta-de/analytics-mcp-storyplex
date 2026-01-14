"""Works endpoints for viewing and managing scraped works."""

from typing import Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from src.db.connection import get_session
from src.db.models import Author, Fandom, Platform, Work, WorkFandom

router = APIRouter()


class WorkSummary(BaseModel):
    """Work summary for list views."""

    id: int
    platform_work_id: str
    title: str
    author_name: Optional[str]
    platform: str
    word_count: int
    chapter_count: int
    views: int
    likes: int
    comments: int
    bookmarks: int
    status: str
    rating: str
    url: str
    fandoms: list[str]


class WorkDetail(BaseModel):
    """Detailed work information."""

    id: int
    platform_work_id: str
    title: str
    summary: Optional[str]
    author_name: Optional[str]
    author_profile_url: Optional[str]
    platform: str
    word_count: int
    chapter_count: int
    views: int
    likes: int
    comments: int
    bookmarks: int
    status: str
    rating: str
    language: str
    url: str
    published_at: Optional[str]
    updated_at: Optional[str]
    scraped_at: str
    fandoms: list[str]
    tags: list[str]
    relationships: list[str]


class WorksResponse(BaseModel):
    """Paginated works response."""

    works: list[WorkSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("", response_model=WorksResponse)
async def list_works(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
    sort_by: str = Query(default="views", regex="^(views|likes|words|updated|created)$"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$"),
    platform: Optional[str] = Query(default=None),
    fandom: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    min_words: Optional[int] = Query(default=None),
    max_words: Optional[int] = Query(default=None),
):
    """List works with pagination and filtering."""
    with get_session() as session:
        query = (
            session.query(Work)
            .outerjoin(Author)
            .outerjoin(Platform)
        )

        # Apply filters
        if platform:
            query = query.filter(Platform.name.ilike(f"%{platform}%"))

        if fandom:
            query = query.join(WorkFandom).join(Fandom).filter(
                Fandom.normalized_name.ilike(f"%{fandom.lower()}%")
            )

        if search:
            query = query.filter(Work.title.ilike(f"%{search}%"))

        if min_words:
            query = query.filter(Work.word_count >= min_words)

        if max_words:
            query = query.filter(Work.word_count <= max_words)

        # Get total count
        total = query.count()

        # Apply sorting
        sort_column = {
            "views": Work.latest_views,
            "likes": Work.latest_likes,
            "words": Work.word_count,
            "updated": Work.updated_at,
            "created": Work.published_at,
        }.get(sort_by, Work.latest_views)

        if sort_order == "desc":
            query = query.order_by(sort_column.desc().nullslast())
        else:
            query = query.order_by(sort_column.asc().nullsfirst())

        # Apply pagination
        offset = (page - 1) * page_size
        works = query.offset(offset).limit(page_size).all()

        # Build response
        work_summaries = []
        for work in works:
            fandom_names = [wf.fandom.name for wf in work.fandoms]
            work_summaries.append(
                WorkSummary(
                    id=work.id,
                    platform_work_id=work.platform_work_id,
                    title=work.title,
                    author_name=work.author.username if work.author else None,
                    platform=work.platform.name if work.platform else "Unknown",
                    word_count=work.word_count,
                    chapter_count=work.chapter_count,
                    views=work.latest_views,
                    likes=work.latest_likes,
                    comments=work.latest_comments,
                    bookmarks=work.latest_bookmarks,
                    status=work.status.value if work.status else "unknown",
                    rating=work.rating.value if work.rating else "not_rated",
                    url=work.url,
                    fandoms=fandom_names,
                )
            )

        return WorksResponse(
            works=work_summaries,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )


@router.get("/{work_id}", response_model=WorkDetail)
async def get_work(work_id: int):
    """Get detailed information about a specific work."""
    with get_session() as session:
        work = session.query(Work).filter(Work.id == work_id).first()

        if not work:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Work not found")

        fandom_names = [wf.fandom.name for wf in work.fandoms]
        tag_names = [wt.tag.name for wt in work.tags]
        rel_names = [wr.relationship.name for wr in work.relationships]

        return WorkDetail(
            id=work.id,
            platform_work_id=work.platform_work_id,
            title=work.title,
            summary=work.summary,
            author_name=work.author.username if work.author else None,
            author_profile_url=work.author.profile_url if work.author else None,
            platform=work.platform.name if work.platform else "Unknown",
            word_count=work.word_count,
            chapter_count=work.chapter_count,
            views=work.latest_views,
            likes=work.latest_likes,
            comments=work.latest_comments,
            bookmarks=work.latest_bookmarks,
            status=work.status.value if work.status else "unknown",
            rating=work.rating.value if work.rating else "not_rated",
            language=work.language,
            url=work.url,
            published_at=work.published_at.isoformat() if work.published_at else None,
            updated_at=work.updated_at.isoformat() if work.updated_at else None,
            scraped_at=work.scraped_at.isoformat() if work.scraped_at else "",
            fandoms=fandom_names,
            tags=tag_names,
            relationships=rel_names,
        )


@router.get("/{work_id}/engagement-history")
async def get_work_engagement_history(work_id: int):
    """Get engagement history for a specific work."""
    from src.db.models import EngagementSnapshot

    with get_session() as session:
        snapshots = (
            session.query(EngagementSnapshot)
            .filter(EngagementSnapshot.work_id == work_id)
            .order_by(EngagementSnapshot.snapshot_date)
            .all()
        )

        return [
            {
                "date": s.snapshot_date.isoformat(),
                "views": s.views,
                "likes": s.likes,
                "comments": s.comments,
                "bookmarks": s.bookmarks,
            }
            for s in snapshots
        ]
