"""MCP Server for Storyplex Analytics.

This server exposes tools for Claude Desktop to:
- Query analytics data
- Search works and fandoms
- Run scrape jobs
- Get insights from the database
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal and datetime types."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj == int(obj) else float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def json_dumps(obj, **kwargs):
    """JSON dumps with custom encoder."""
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)


def log_error(message: str):
    """Log error to stderr (won't interfere with MCP JSON protocol)."""
    print(f"[ERROR] {message}", file=sys.stderr)


def log_info(message: str):
    """Log info to stderr."""
    print(f"[INFO] {message}", file=sys.stderr)


async def with_timeout(coro, timeout_seconds: int = 120, operation: str = "operation"):
    """Execute a coroutine with a timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise TimeoutError(f"{operation} timed out after {timeout_seconds} seconds")


async def run_with_retry(
    func: Callable,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    operation: str = "operation",
):
    """Run a blocking function in a thread with retry logic."""
    last_error = None
    for attempt in range(max_retries):
        try:
            result = await asyncio.to_thread(func)
            return result
        except Exception as e:
            last_error = e
            log_error(f"{operation} attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
    raise last_error

from mcp.server import Server  # noqa: E402
from mcp.server.stdio import stdio_server  # noqa: E402
from mcp.types import TextContent, Tool  # noqa: E402
from sqlalchemy import func  # noqa: E402

from src.db.connection import get_session  # noqa: E402
from src.db.models import (  # noqa: E402
    Author,
    Fandom,
    PlatformType,
    Tag,
    Work,
    WorkFandom,
    WorkTag,
)
from src.db.repository import WorkRepository  # noqa: E402
from src.scrapers.ao3 import AO3Scraper  # noqa: E402

# Create the MCP server
server = Server("storyplex-analytics")

# LLM Service (lazy initialization)
_llm_service = None


def get_llm_service():
    """Get or create the LLM service instance."""
    global _llm_service
    if _llm_service is None:
        from src.llm import LLMService
        _llm_service = LLMService()
    return _llm_service


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_analytics_summary",
            description="Get overall analytics summary including total works, authors, fandoms, views, etc.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="search_works",
            description="Search for works in the database. Returns matching works with stats.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for title",
                    },
                    "fandom": {
                        "type": "string",
                        "description": "Filter by fandom name",
                    },
                    "min_views": {
                        "type": "integer",
                        "description": "Minimum view count",
                    },
                    "min_likes": {
                        "type": "integer",
                        "description": "Minimum likes/kudos count",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 20)",
                        "default": 20,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_top_fandoms",
            description="Get top fandoms by work count, views, or likes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sort_by": {
                        "type": "string",
                        "enum": ["works", "views", "likes"],
                        "description": "How to sort fandoms",
                        "default": "works",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 20)",
                        "default": 20,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_top_tags",
            description="Get most popular tags across all works.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by tag category (freeform, warning, etc.)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 30)",
                        "default": 30,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="scrape_ao3_works",
            description="Scrape works from Archive of Our Own. This will fetch and store works in the database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "fandom": {
                        "type": "string",
                        "description": "Fandom to scrape (e.g., 'Harry Potter')",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["kudos", "hits", "bookmarks", "date"],
                        "description": "How to sort results",
                        "default": "kudos",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max works to scrape (default 50)",
                        "default": 50,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="scrape_ao3_fandoms",
            description="Scrape top fandoms from AO3 media page and store in database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max fandoms to scrape (default 100)",
                        "default": 100,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="analyze_fandom",
            description="[LLM-POWERED] Get detailed analytics for ANY fandom. Tries database first, then live scraping, then AI analysis. Never fails to return insights.",
            inputSchema={
                "type": "object",
                "properties": {
                    "fandom_name": {
                        "type": "string",
                        "description": "Name of the fandom to analyze (e.g., 'My Hero Academia', 'Genshin Impact', 'Supernatural')",
                    },
                },
                "required": ["fandom_name"],
            },
        ),
        Tool(
            name="get_fandom_genres",
            description="[LLM-POWERED] Get popular genres/tags, relationships, and characters for ANY fandom. Smart name matching + LLM fallback ensures results for any query.",
            inputSchema={
                "type": "object",
                "properties": {
                    "fandom_name": {
                        "type": "string",
                        "description": "Name of the fandom (e.g., 'Harry Potter - J. K. Rowling', 'Marvel Cinematic Universe')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max tags to return per category (default 15)",
                        "default": 15,
                    },
                },
                "required": ["fandom_name"],
            },
        ),
        Tool(
            name="estimate_fandom_time",
            description="[LLM-POWERED] Estimate time needed to consume source material for ANY fandom (books, movies, anime, games, etc). Uses AI to provide accurate estimates for any fandom.",
            inputSchema={
                "type": "object",
                "properties": {
                    "fandom_name": {
                        "type": "string",
                        "description": "Name of the fandom to estimate (e.g., 'Final Fantasy', 'One Piece', 'Game of Thrones')",
                    },
                },
                "required": ["fandom_name"],
            },
        ),
        Tool(
            name="analyze_fandom_insights",
            description="[LLM-POWERED] Get deep AI-powered insights about a fandom's fanfiction landscape. Analyzes genres, tropes, shipping culture, and identifies writing opportunities.",
            inputSchema={
                "type": "object",
                "properties": {
                    "fandom_name": {
                        "type": "string",
                        "description": "Name of the fandom (e.g., 'Harry Potter - J. K. Rowling', 'Marvel Cinematic Universe')",
                    },
                },
                "required": ["fandom_name"],
            },
        ),
        Tool(
            name="analyze_market_trends",
            description="[LLM-POWERED] Analyze fanfiction market trends and get strategic insights. Can answer specific questions about the market.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Optional specific question about the market (e.g., 'Which anime fandoms are growing fastest?')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top fandoms to analyze (default 50)",
                        "default": 50,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="run_custom_query",
            description="[LLM-POWERED] Answer ANY analytics question about fanfiction, fandoms, or web novels. Uses AI + live data to provide comprehensive answers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Any question about fanfiction analytics (e.g., 'What are the top anime fandoms?', 'Which genres are most popular?')",
                    },
                },
                "required": ["question"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls with comprehensive error handling."""
    log_info(f"Tool called: {name} with args: {arguments}")

    try:
        return await _handle_tool(name, arguments)
    except TimeoutError as e:
        log_error(f"Timeout in {name}: {e}")
        return [TextContent(type="text", text=f"Error: Operation timed out. {str(e)}")]
    except Exception as e:
        log_error(f"Error in {name}: {e}\n{traceback.format_exc()}")
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


async def _handle_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Internal tool handler."""

    if name == "get_analytics_summary":
        with get_session() as session:
            result = {
                "total_works": session.query(func.count(Work.id)).scalar() or 0,
                "total_authors": session.query(func.count(Author.id)).scalar() or 0,
                "total_fandoms": session.query(func.count(Fandom.id)).scalar() or 0,
                "total_tags": session.query(func.count(Tag.id)).scalar() or 0,
                "total_words": session.query(func.sum(Work.word_count)).scalar() or 0,
                "total_views": session.query(func.sum(Work.latest_views)).scalar() or 0,
                "total_likes": session.query(func.sum(Work.latest_likes)).scalar() or 0,
            }
        return [TextContent(type="text", text=json_dumps(result, indent=2))]

    elif name == "search_works":
        with get_session() as session:
            query = session.query(Work)

            if arguments.get("query"):
                query = query.filter(Work.title.ilike(f"%{arguments['query']}%"))

            if arguments.get("fandom"):
                query = (
                    query.join(WorkFandom)
                    .join(Fandom)
                    .filter(Fandom.normalized_name.ilike(f"%{arguments['fandom'].lower()}%"))
                )

            if arguments.get("min_views"):
                query = query.filter(Work.latest_views >= arguments["min_views"])

            if arguments.get("min_likes"):
                query = query.filter(Work.latest_likes >= arguments["min_likes"])

            limit = arguments.get("limit", 20)
            works = query.order_by(Work.latest_views.desc()).limit(limit).all()

            results = []
            for w in works:
                fandoms = [wf.fandom.name for wf in w.fandoms]
                results.append({
                    "id": w.id,
                    "title": w.title,
                    "author": w.author.username if w.author else None,
                    "fandoms": fandoms,
                    "word_count": w.word_count,
                    "views": w.latest_views,
                    "likes": w.latest_likes,
                    "url": w.url,
                })

        return [TextContent(type="text", text=json_dumps(results, indent=2))]

    elif name == "get_top_fandoms":
        sort_by = arguments.get("sort_by", "works")
        limit = arguments.get("limit", 20)

        with get_session() as session:
            # Query fandoms with their AO3 estimated work count and our scraped stats
            query = (
                session.query(
                    Fandom.name,
                    Fandom.category,
                    Fandom.estimated_work_count,
                    func.count(WorkFandom.work_id).label("scraped_works"),
                    func.coalesce(func.sum(Work.latest_views), 0).label("total_views"),
                    func.coalesce(func.sum(Work.latest_likes), 0).label("total_likes"),
                )
                .outerjoin(WorkFandom, Fandom.id == WorkFandom.fandom_id)
                .outerjoin(Work, WorkFandom.work_id == Work.id)
                .group_by(Fandom.id)
            )

            if sort_by == "views":
                query = query.order_by(func.sum(Work.latest_views).desc())
            elif sort_by == "likes":
                query = query.order_by(func.sum(Work.latest_likes).desc())
            else:
                # Sort by AO3's estimated work count by default
                query = query.order_by(Fandom.estimated_work_count.desc())

            results = query.limit(limit).all()

            data = [
                {
                    "name": r.name,
                    "category": r.category,
                    "ao3_work_count": r.estimated_work_count,
                    "scraped_works": r.scraped_works,
                    "total_views": r.total_views,
                    "total_likes": r.total_likes,
                }
                for r in results
            ]

        return [TextContent(type="text", text=json_dumps(data, indent=2))]

    elif name == "get_top_tags":
        limit = arguments.get("limit", 30)
        category = arguments.get("category")

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

            data = [
                {"name": r.name, "category": r.category, "work_count": r.work_count}
                for r in results
            ]

        return [TextContent(type="text", text=json_dumps(data, indent=2))]

    elif name == "scrape_ao3_works":
        fandom = arguments.get("fandom")
        sort_by = arguments.get("sort_by", "kudos")
        limit = arguments.get("limit", 50)

        def _scrape_works():
            try:
                with AO3Scraper() as scraper:
                    with get_session() as session:
                        repo = WorkRepository(session)
                        platform = repo.get_or_create_platform(PlatformType.AO3, scraper.base_url)

                        count = 0
                        for scraped_work in scraper.search_works(
                            fandom=fandom,
                            sort_by=sort_by,
                            limit=limit,
                        ):
                            work = repo.upsert_work(scraped_work, platform)
                            repo.create_engagement_snapshot(work)
                            count += 1
                        return count
            except Exception as e:
                log_error(f"Scraper error: {e}")
                raise

        count = await run_with_retry(
            _scrape_works,
            max_retries=2,
            retry_delay=5.0,
            operation="scrape_ao3_works",
        )
        return [TextContent(type="text", text=f"Successfully scraped {count} works from AO3.")]

    elif name == "scrape_ao3_fandoms":
        limit = arguments.get("limit", 100)

        def _scrape_fandoms():
            try:
                with AO3Scraper() as scraper:
                    fandoms = scraper.get_top_fandoms(limit=limit)

                    if not fandoms:
                        log_error("No fandoms returned from scraper")
                        raise ValueError("Failed to fetch fandoms from AO3 - page may have changed or blocked")

                    with get_session() as session:
                        repo = WorkRepository(session)
                        for fandom in fandoms:
                            repo.get_or_create_fandom(
                                fandom["name"],
                                category=fandom.get("category"),
                                estimated_work_count=fandom.get("work_count", 0),
                            )
                    return fandoms  # Return full data for display
            except Exception as e:
                log_error(f"Fandom scraper error: {e}")
                raise

        fandoms = await run_with_retry(
            _scrape_fandoms,
            max_retries=2,
            retry_delay=5.0,
            operation="scrape_ao3_fandoms",
        )

        # Format response with top fandoms preview
        top_5 = fandoms[:5]
        preview = "\n".join([f"  - {f['name']}: {f['work_count']:,} works" for f in top_5])
        return [TextContent(
            type="text",
            text=f"Successfully scraped {len(fandoms)} fandoms from AO3.\n\nTop 5:\n{preview}"
        )]

    elif name == "analyze_fandom":
        fandom_name = arguments["fandom_name"]

        db_result = None
        scraped_data = None

        # First, try to get from database
        with get_session() as session:
            fandom = (
                session.query(Fandom)
                .filter(Fandom.normalized_name.ilike(f"%{fandom_name.lower()}%"))
                .first()
            )

            if fandom:
                works = (
                    session.query(Work)
                    .join(WorkFandom)
                    .filter(WorkFandom.fandom_id == fandom.id)
                    .all()
                )

                if works:
                    total_views = sum(w.latest_views for w in works)
                    total_likes = sum(w.latest_likes for w in works)
                    avg_words = sum(w.word_count for w in works) / len(works)
                    top_works = sorted(works, key=lambda w: w.latest_views, reverse=True)[:5]

                    tag_counts: dict[str, int] = {}
                    for work in works:
                        for wt in work.tags:
                            tag_counts[wt.tag.name] = tag_counts.get(wt.tag.name, 0) + 1
                    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

                    db_result = {
                        "fandom": fandom.name,
                        "category": fandom.category,
                        "total_works_scraped": len(works),
                        "ao3_work_count": fandom.estimated_work_count,
                        "total_views": total_views,
                        "total_likes": total_likes,
                        "avg_word_count": round(avg_words),
                        "top_works": [
                            {"title": w.title, "views": w.latest_views, "likes": w.latest_likes}
                            for w in top_works
                        ],
                        "top_tags": [{"tag": t[0], "count": t[1]} for t in top_tags],
                        "source": "database"
                    }

        # If no DB data, try to scrape genre stats from AO3
        if not db_result:
            log_info(f"No DB data for '{fandom_name}', trying to scrape...")

            # Use LLM to find correct AO3 name
            ao3_name = fandom_name
            try:
                def _find_name():
                    llm = get_llm_service()
                    return llm.find_ao3_fandom_name(fandom_name)
                ao3_name = await asyncio.to_thread(_find_name)
            except Exception:
                pass

            # Try to scrape
            def _scrape():
                with AO3Scraper() as scraper:
                    return scraper.get_fandom_tag_stats(ao3_name)

            try:
                scraped_data = await asyncio.to_thread(_scrape)
                if scraped_data.get("total_works", 0) > 0:
                    db_result = {
                        "fandom": fandom_name,
                        "ao3_tag": ao3_name,
                        "total_works": scraped_data["total_works"],
                        "top_genres": scraped_data.get("genres", [])[:10],
                        "top_relationships": scraped_data.get("relationships", [])[:10],
                        "ratings": scraped_data.get("ratings", []),
                        "source": "AO3 live scrape"
                    }
            except Exception as e:
                log_error(f"Scrape failed: {e}")

        # If still no data, use LLM to generate analysis
        if not db_result:
            log_info(f"Using LLM analysis for '{fandom_name}'")

            def _generate():
                try:
                    llm = get_llm_service()
                    return llm.generate_fandom_analysis(fandom_name, scraped_data)
                except ValueError as e:
                    return {"error": str(e)}
                except Exception as e:
                    return {"error": str(e)}

            db_result = await asyncio.to_thread(_generate)

            if "error" not in db_result:
                db_result["source"] = "LLM knowledge"

        if "error" in db_result:
            return [TextContent(type="text", text=f"Could not analyze '{fandom_name}': {db_result['error']}")]

        return [TextContent(type="text", text=json_dumps(db_result, indent=2))]

    elif name == "get_fandom_genres":
        fandom_name = arguments["fandom_name"]
        limit = arguments.get("limit", 15)

        # First, try to find the correct AO3 fandom name using LLM
        ao3_fandom_name = fandom_name
        try:
            def _find_name():
                llm = get_llm_service()
                return llm.find_ao3_fandom_name(fandom_name)
            ao3_fandom_name = await asyncio.to_thread(_find_name)
            log_info(f"Mapped '{fandom_name}' -> '{ao3_fandom_name}'")
        except Exception as e:
            log_error(f"Name lookup failed, using original: {e}")

        # Try multiple name variations
        names_to_try = [ao3_fandom_name]
        if ao3_fandom_name != fandom_name:
            names_to_try.append(fandom_name)

        stats = None

        for name_attempt in names_to_try:
            def _get_fandom_genres(name=name_attempt):
                with AO3Scraper() as scraper:
                    return scraper.get_fandom_tag_stats(name)

            try:
                stats = await run_with_retry(
                    _get_fandom_genres,
                    max_retries=2,
                    retry_delay=3.0,
                    operation="get_fandom_genres",
                )
                if stats.get("total_works", 0) > 0 or stats.get("genres"):
                    break  # Success!
                stats = None
            except Exception as e:
                log_error(f"Failed with name '{name_attempt}': {e}")

        # If scraping failed, fall back to LLM-generated analysis
        if not stats or (stats.get("total_works", 0) == 0 and not stats.get("genres")):
            log_info(f"Scraping failed, using LLM analysis for '{fandom_name}'")

            def _generate_analysis():
                try:
                    llm = get_llm_service()
                    return llm.generate_fandom_analysis(fandom_name, stats)
                except ValueError as e:
                    return {"error": str(e)}
                except Exception as e:
                    return {"error": str(e)}

            result = await asyncio.to_thread(_generate_analysis)

            if "error" in result:
                return [TextContent(
                    type="text",
                    text=f"Could not scrape or analyze '{fandom_name}': {result['error']}"
                )]

            result["source"] = "LLM knowledge (scraping failed)"
            return [TextContent(type="text", text=json_dumps(result, indent=2))]

        # Format the scraped result
        result = {
            "fandom": stats["fandom"],
            "total_works": stats["total_works"],
            "top_genres": stats["genres"][:limit],
            "top_relationships": stats["relationships"][:limit],
            "top_characters": stats["characters"][:limit],
            "ratings": stats["ratings"],
            "categories": stats["categories"],
            "source": "AO3 scraped data"
        }

        return [TextContent(type="text", text=json_dumps(result, indent=2))]

    elif name == "estimate_fandom_time":
        fandom_name = arguments["fandom_name"]

        # Use LLM to generate intelligent time estimates for ANY fandom
        def _estimate_time():
            try:
                llm = get_llm_service()
                return llm.estimate_fandom_time(fandom_name)
            except ValueError as e:
                # API key not configured
                log_error(f"LLM not configured: {e}")
                return {
                    "fandom": fandom_name,
                    "error": str(e),
                    "suggestion": "Set ANTHROPIC_API_KEY environment variable to enable LLM-powered estimates",
                }
            except Exception as e:
                log_error(f"LLM error: {e}")
                return {"fandom": fandom_name, "error": str(e)}

        result = await asyncio.to_thread(_estimate_time)
        return [TextContent(type="text", text=json_dumps(result, indent=2))]

    elif name == "analyze_fandom_insights":
        fandom_name = arguments["fandom_name"]

        # First, scrape genre data from AO3
        def _get_genre_data():
            with AO3Scraper() as scraper:
                return scraper.get_fandom_tag_stats(fandom_name)

        try:
            genre_data = await run_with_retry(
                _get_genre_data,
                max_retries=2,
                retry_delay=5.0,
                operation="get_fandom_genres",
            )
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error fetching genre data for '{fandom_name}': {str(e)}\n\nTip: Use the exact fandom name as it appears on AO3."
            )]

        if "error" in genre_data:
            return [TextContent(type="text", text=f"Error: {genre_data['error']}")]

        # Now analyze with LLM
        def _analyze():
            try:
                llm = get_llm_service()
                return llm.analyze_fandom_genres(fandom_name, genre_data)
            except ValueError as e:
                return {"error": str(e)}
            except Exception as e:
                log_error(f"LLM analysis error: {e}")
                return {"error": str(e)}

        analysis = await asyncio.to_thread(_analyze)

        if "error" in analysis:
            return [TextContent(type="text", text=f"Error analyzing fandom: {analysis['error']}")]

        # Combine raw data with analysis
        result = {
            "fandom": fandom_name,
            "total_works": genre_data.get("total_works", 0),
            "ai_analysis": analysis,
            "raw_data": {
                "top_genres": genre_data.get("genres", [])[:10],
                "top_relationships": genre_data.get("relationships", [])[:10],
                "ratings": genre_data.get("ratings", []),
            },
        }

        return [TextContent(type="text", text=json_dumps(result, indent=2))]

    elif name == "analyze_market_trends":
        question = arguments.get("question")
        limit = arguments.get("limit", 50)

        # Get top fandoms from database or scrape fresh
        def _get_fandoms():
            with get_session() as session:
                fandoms = (
                    session.query(Fandom)
                    .order_by(Fandom.estimated_work_count.desc())
                    .limit(limit)
                    .all()
                )
                if fandoms and fandoms[0].estimated_work_count > 0:
                    return [
                        {
                            "name": f.name,
                            "work_count": f.estimated_work_count,
                            "category": f.category,
                        }
                        for f in fandoms
                    ]
            # No data in DB, scrape fresh
            with AO3Scraper() as scraper:
                return scraper.get_top_fandoms(limit=limit)

        try:
            fandoms = await run_with_retry(
                _get_fandoms,
                max_retries=2,
                retry_delay=3.0,
                operation="get_fandoms",
            )
        except Exception as e:
            return [TextContent(type="text", text=f"Error fetching fandom data: {e}")]

        if not fandoms:
            return [TextContent(type="text", text="No fandom data available. Run scrape_ao3_fandoms first.")]

        # Analyze with LLM
        def _analyze():
            try:
                llm = get_llm_service()
                return llm.analyze_market_trends(fandoms, question)
            except ValueError as e:
                return {"error": str(e)}
            except Exception as e:
                log_error(f"LLM analysis error: {e}")
                return {"error": str(e)}

        analysis = await asyncio.to_thread(_analyze)

        if "error" in analysis:
            return [TextContent(type="text", text=f"Error analyzing market: {analysis['error']}")]

        return [TextContent(type="text", text=json_dumps(analysis, indent=2))]

    elif name == "run_custom_query":
        question = arguments["question"]

        # Gather context from database and scraper
        db_data = {}
        scraped_data = {}

        # Get database stats
        try:
            with get_session() as session:
                db_data["total_works"] = session.query(func.count(Work.id)).scalar() or 0
                db_data["total_fandoms"] = session.query(func.count(Fandom.id)).scalar() or 0

                # Get top fandoms from DB
                top_fandoms = (
                    session.query(Fandom)
                    .order_by(Fandom.estimated_work_count.desc())
                    .limit(20)
                    .all()
                )
                if top_fandoms:
                    db_data["top_fandoms"] = [
                        {"name": f.name, "work_count": f.estimated_work_count, "category": f.category}
                        for f in top_fandoms
                    ]
        except Exception as e:
            log_error(f"DB query error: {e}")

        # Try to scrape fresh data if question mentions anime/fandoms
        question_lower = question.lower()
        if any(kw in question_lower for kw in ["anime", "fandom", "top", "popular", "trending"]):
            try:
                def _scrape_fandoms():
                    with AO3Scraper() as scraper:
                        return scraper.get_top_fandoms(limit=30)

                fandoms = await asyncio.to_thread(_scrape_fandoms)
                if fandoms:
                    scraped_data["ao3_top_fandoms"] = fandoms
            except Exception as e:
                log_error(f"Scrape error: {e}")

        # Use LLM to answer the question
        def _answer():
            try:
                llm = get_llm_service()
                return llm.answer_any_question(question, scraped_data, db_data)
            except ValueError as e:
                # LLM not configured - still try to answer using basic knowledge
                return {
                    "error": str(e),
                    "suggestion": "Configure ANTHROPIC_API_KEY for full AI-powered answers"
                }
            except Exception as e:
                log_error(f"LLM error: {e}")
                return {"error": str(e)}

        result = await asyncio.to_thread(_answer)

        if "error" in result and "ANTHROPIC_API_KEY" not in str(result.get("error", "")):
            return [TextContent(type="text", text=f"Error: {result['error']}")]

        return [TextContent(type="text", text=json_dumps(result, indent=2))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
