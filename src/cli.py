"""CLI for Storyplex Analytics scrapers."""

import click
from rich.console import Console
from rich.table import Table

from src.db.connection import get_session, init_db
from src.db.models import PlatformType
from src.db.repository import WorkRepository
from src.scrapers.ao3 import AO3Scraper

console = Console()


@click.group()
def main():
    """Storyplex Analytics - Multi-platform fanfiction scraper."""
    pass


@main.command()
def init():
    """Initialize the database tables."""
    console.print("[blue]Initializing database...[/blue]")
    init_db()
    console.print("[green]Database initialized successfully![/green]")


@main.group()
def scrape():
    """Scrape data from various platforms."""
    pass


@scrape.command("ao3")
@click.option("--fandom", "-f", help="Filter by fandom name")
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--query", "-q", help="Search query")
@click.option("--sort", "-s", default="kudos", help="Sort by: kudos, hits, bookmarks, date, words")
@click.option("--limit", "-l", default=100, help="Maximum number of works to scrape")
@click.option("--snapshot/--no-snapshot", default=True, help="Create engagement snapshots")
def scrape_ao3(fandom, tag, query, sort, limit, snapshot):
    """Scrape works from Archive of Our Own."""
    console.print(f"[blue]Starting AO3 scrape (limit: {limit})...[/blue]")

    with AO3Scraper() as scraper:
        with get_session() as session:
            repo = WorkRepository(session)
            platform = repo.get_or_create_platform(PlatformType.AO3, scraper.base_url)

            count = 0
            for scraped_work in scraper.search_works(
                query=query,
                fandom=fandom,
                tag=tag,
                sort_by=sort,
                limit=limit,
            ):
                work = repo.upsert_work(scraped_work, platform)
                if snapshot:
                    repo.create_engagement_snapshot(work)
                count += 1

            console.print(f"[green]Saved {count} works to database[/green]")


@scrape.command("ao3-work")
@click.argument("work_id")
@click.option("--snapshot/--no-snapshot", default=True, help="Create engagement snapshot")
def scrape_ao3_work(work_id, snapshot):
    """Scrape a single AO3 work by ID."""
    console.print(f"[blue]Scraping AO3 work {work_id}...[/blue]")

    with AO3Scraper() as scraper:
        scraped_work = scraper.scrape_work(work_id)

        if not scraped_work:
            console.print(f"[red]Work {work_id} not found[/red]")
            return

        with get_session() as session:
            repo = WorkRepository(session)
            platform = repo.get_or_create_platform(PlatformType.AO3, scraper.base_url)

            work = repo.upsert_work(scraped_work, platform)
            if snapshot:
                repo.create_engagement_snapshot(work)

            console.print(f"[green]Saved work: {work.title}[/green]")


@scrape.command("ao3-fandoms")
@click.option("--limit", "-l", default=100, help="Maximum number of fandoms to fetch")
@click.option("--save/--no-save", default=True, help="Save fandoms to database")
def scrape_ao3_fandoms(limit, save):
    """Scrape top fandoms from AO3 media page."""
    console.print(f"[blue]Fetching top {limit} fandoms from AO3...[/blue]")

    with AO3Scraper() as scraper:
        fandoms = scraper.get_top_fandoms(limit=limit)

        if not fandoms:
            console.print("[red]No fandoms found[/red]")
            return

        # Display table
        table = Table(title=f"Top {len(fandoms)} AO3 Fandoms")
        table.add_column("#", style="dim")
        table.add_column("Fandom", style="cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Works", style="green", justify="right")

        for i, fandom in enumerate(fandoms[:50], 1):  # Show top 50 in table
            table.add_row(
                str(i),
                fandom["name"],
                fandom.get("category", "")[:20] if fandom.get("category") else "",
                f"{fandom['work_count']:,}",
            )

        console.print(table)

        if save:
            with get_session() as session:
                repo = WorkRepository(session)
                for fandom in fandoms:
                    repo.get_or_create_fandom(fandom["name"])
                console.print(f"[green]Saved {len(fandoms)} fandoms to database[/green]")


@main.group()
def stats():
    """View statistics from the database."""
    pass


@stats.command("summary")
def stats_summary():
    """Show summary statistics."""
    from sqlalchemy import func

    from src.db.models import Author, Fandom, Tag, Work

    with get_session() as session:
        work_count = session.query(func.count(Work.id)).scalar()
        author_count = session.query(func.count(Author.id)).scalar()
        fandom_count = session.query(func.count(Fandom.id)).scalar()
        tag_count = session.query(func.count(Tag.id)).scalar()

        total_words = session.query(func.sum(Work.word_count)).scalar() or 0
        total_views = session.query(func.sum(Work.latest_views)).scalar() or 0

        table = Table(title="Storyplex Analytics Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Works", f"{work_count:,}")
        table.add_row("Total Authors", f"{author_count:,}")
        table.add_row("Total Fandoms", f"{fandom_count:,}")
        table.add_row("Total Tags", f"{tag_count:,}")
        table.add_row("Total Words", f"{total_words:,}")
        table.add_row("Total Views", f"{total_views:,}")

        console.print(table)


@stats.command("top-works")
@click.option("--by", "-b", default="views", help="Sort by: views, likes, words, bookmarks")
@click.option("--limit", "-l", default=10, help="Number of works to show")
def stats_top_works(by, limit):
    """Show top works by various metrics."""
    from src.db.models import Work

    sort_column = {
        "views": Work.latest_views,
        "likes": Work.latest_likes,
        "words": Work.word_count,
        "bookmarks": Work.latest_bookmarks,
    }.get(by, Work.latest_views)

    with get_session() as session:
        works = session.query(Work).order_by(sort_column.desc()).limit(limit).all()

        table = Table(title=f"Top {limit} Works by {by.capitalize()}")
        table.add_column("#", style="dim")
        table.add_column("Title", style="cyan", max_width=40)
        table.add_column("Views", style="green", justify="right")
        table.add_column("Likes", style="yellow", justify="right")
        table.add_column("Words", style="blue", justify="right")

        for i, work in enumerate(works, 1):
            table.add_row(
                str(i),
                work.title[:40] + "..." if len(work.title) > 40 else work.title,
                f"{work.latest_views:,}",
                f"{work.latest_likes:,}",
                f"{work.word_count:,}",
            )

        console.print(table)


@stats.command("top-fandoms")
@click.option("--limit", "-l", default=10, help="Number of fandoms to show")
def stats_top_fandoms(limit):
    """Show top fandoms by work count."""
    from sqlalchemy import func

    from src.db.models import Fandom, WorkFandom

    with get_session() as session:
        results = (
            session.query(
                Fandom.name,
                func.count(WorkFandom.work_id).label("work_count"),
            )
            .join(WorkFandom)
            .group_by(Fandom.id)
            .order_by(func.count(WorkFandom.work_id).desc())
            .limit(limit)
            .all()
        )

        table = Table(title=f"Top {limit} Fandoms")
        table.add_column("#", style="dim")
        table.add_column("Fandom", style="cyan")
        table.add_column("Works", style="green", justify="right")

        for i, (name, count) in enumerate(results, 1):
            table.add_row(str(i), name, f"{count:,}")

        console.print(table)


if __name__ == "__main__":
    main()
