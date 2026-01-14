"""Jobs endpoints for managing scrape jobs."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter()


class JobStatus(str, Enum):
    """Job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type."""

    SCRAPE_WORKS = "scrape_works"
    SCRAPE_FANDOMS = "scrape_fandoms"
    SCRAPE_SINGLE_WORK = "scrape_single_work"


# In-memory job store (in production, use Redis or database)
jobs_store: dict[str, dict] = {}


class ScrapeJobRequest(BaseModel):
    """Request to start a scrape job."""

    platform: str = "ao3"
    job_type: JobType = JobType.SCRAPE_WORKS
    fandom: Optional[str] = None
    tag: Optional[str] = None
    query: Optional[str] = None
    sort_by: str = "kudos"
    limit: int = 100
    work_id: Optional[str] = None  # For single work scrapes


class JobResponse(BaseModel):
    """Job response."""

    id: str
    status: JobStatus
    job_type: JobType
    platform: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    progress: int
    total: int
    error: Optional[str]
    result: Optional[dict]


def run_scrape_job(job_id: str, request: ScrapeJobRequest):
    """Run a scrape job in the background."""
    from src.db.connection import get_session
    from src.db.models import PlatformType
    from src.db.repository import WorkRepository
    from src.scrapers.ao3 import AO3Scraper

    job = jobs_store.get(job_id)
    if not job:
        return

    job["status"] = JobStatus.RUNNING
    job["started_at"] = datetime.utcnow().isoformat()

    try:
        if request.platform.lower() == "ao3":
            with AO3Scraper() as scraper:
                if request.job_type == JobType.SCRAPE_FANDOMS:
                    # Scrape fandoms
                    fandoms = scraper.get_top_fandoms(limit=request.limit)
                    job["total"] = len(fandoms)

                    with get_session() as session:
                        repo = WorkRepository(session)
                        for i, fandom in enumerate(fandoms):
                            repo.get_or_create_fandom(
                                fandom["name"],
                                category=fandom.get("category"),
                            )
                            job["progress"] = i + 1

                    job["result"] = {"fandoms_scraped": len(fandoms)}

                elif request.job_type == JobType.SCRAPE_SINGLE_WORK:
                    # Scrape single work
                    if not request.work_id:
                        raise ValueError("work_id is required for single work scrape")

                    job["total"] = 1
                    scraped_work = scraper.scrape_work(request.work_id)

                    if scraped_work:
                        with get_session() as session:
                            repo = WorkRepository(session)
                            platform = repo.get_or_create_platform(
                                PlatformType.AO3, scraper.base_url
                            )
                            work = repo.upsert_work(scraped_work, platform)
                            repo.create_engagement_snapshot(work)

                        job["progress"] = 1
                        job["result"] = {
                            "work_id": work.id,
                            "title": scraped_work.title,
                        }
                    else:
                        raise ValueError(f"Work {request.work_id} not found")

                else:
                    # Scrape works
                    job["total"] = request.limit
                    count = 0

                    with get_session() as session:
                        repo = WorkRepository(session)
                        platform = repo.get_or_create_platform(
                            PlatformType.AO3, scraper.base_url
                        )

                        for scraped_work in scraper.search_works(
                            query=request.query,
                            fandom=request.fandom,
                            tag=request.tag,
                            sort_by=request.sort_by,
                            limit=request.limit,
                        ):
                            work = repo.upsert_work(scraped_work, platform)
                            repo.create_engagement_snapshot(work)
                            count += 1
                            job["progress"] = count

                    job["result"] = {"works_scraped": count}

        job["status"] = JobStatus.COMPLETED
        job["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        job["status"] = JobStatus.FAILED
        job["error"] = str(e)
        job["completed_at"] = datetime.utcnow().isoformat()


@router.post("", response_model=JobResponse)
async def create_job(request: ScrapeJobRequest, background_tasks: BackgroundTasks):
    """Start a new scrape job."""
    job_id = str(uuid.uuid4())

    job = {
        "id": job_id,
        "status": JobStatus.PENDING,
        "job_type": request.job_type,
        "platform": request.platform,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None,
        "progress": 0,
        "total": request.limit,
        "error": None,
        "result": None,
        "request": request.model_dump(),
    }

    jobs_store[job_id] = job

    # Start background task
    background_tasks.add_task(run_scrape_job, job_id, request)

    return JobResponse(**job)


@router.get("", response_model=list[JobResponse])
async def list_jobs(limit: int = 20):
    """List recent jobs."""
    jobs = sorted(
        jobs_store.values(),
        key=lambda x: x["created_at"],
        reverse=True,
    )[:limit]

    return [JobResponse(**job) for job in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job status."""
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(**job)


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a job (only pending jobs can be cancelled)."""
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == JobStatus.PENDING:
        job["status"] = JobStatus.CANCELLED
        return {"message": "Job cancelled"}
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status {job['status']}",
        )


@router.get("/platforms/available")
async def get_available_platforms():
    """Get list of available platforms for scraping."""
    return [
        {
            "id": "ao3",
            "name": "Archive of Our Own",
            "supports_fandoms": True,
            "supports_tags": True,
            "supports_search": True,
            "rate_limit": "1 req / 5 sec",
        },
        # Future platforms
        {
            "id": "royalroad",
            "name": "Royal Road",
            "supports_fandoms": False,
            "supports_tags": True,
            "supports_search": True,
            "rate_limit": "1 req / sec",
            "status": "coming_soon",
        },
        {
            "id": "ffn",
            "name": "FanFiction.net",
            "supports_fandoms": True,
            "supports_tags": False,
            "supports_search": True,
            "rate_limit": "varies",
            "status": "coming_soon",
        },
    ]
