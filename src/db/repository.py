"""Repository for persisting scraped data to the database."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Session

from src.db.models import (
    Author,
    ContentRating,
    EngagementSnapshot,
    Fandom,
    Platform,
    PlatformType,
    Relationship,
    Tag,
    Work,
    WorkFandom,
    WorkRelationship,
    WorkStatus,
    WorkTag,
)

if TYPE_CHECKING:
    from src.scrapers.base import ScrapedWork


class WorkRepository:
    """Repository for work-related database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_or_create_platform(self, platform_type: PlatformType, base_url: str) -> Platform:
        """Get or create a platform record."""
        platform = (
            self.session.query(Platform)
            .filter(Platform.platform_type == platform_type)
            .first()
        )

        if not platform:
            platform = Platform(
                name=platform_type.value.upper(),
                platform_type=platform_type,
                base_url=base_url,
            )
            self.session.add(platform)
            self.session.flush()

        return platform

    def get_or_create_author(
        self,
        platform_id: int,
        platform_author_id: str,
        username: str,
        display_name: Optional[str] = None,
        profile_url: Optional[str] = None,
        bio: Optional[str] = None,
        patreon_url: Optional[str] = None,
        kofi_url: Optional[str] = None,
    ) -> Author:
        """Get or create an author record."""
        author = (
            self.session.query(Author)
            .filter(
                Author.platform_id == platform_id,
                Author.platform_author_id == platform_author_id,
            )
            .first()
        )

        if not author:
            author = Author(
                platform_id=platform_id,
                platform_author_id=platform_author_id,
                username=username,
                display_name=display_name,
                profile_url=profile_url,
                bio=bio,
                patreon_url=patreon_url,
                kofi_url=kofi_url,
            )
            self.session.add(author)
            self.session.flush()
        else:
            # Update existing author with new info if available
            if display_name:
                author.display_name = display_name
            if profile_url:
                author.profile_url = profile_url
            if bio:
                author.bio = bio
            if patreon_url:
                author.patreon_url = patreon_url
            if kofi_url:
                author.kofi_url = kofi_url
            author.updated_at = datetime.utcnow()

        return author

    def get_or_create_tag(
        self, name: str, category: Optional[str] = None
    ) -> Tag:
        """Get or create a tag record."""
        normalized = name.lower().strip()

        tag = (
            self.session.query(Tag)
            .filter(Tag.normalized_name == normalized, Tag.category == category)
            .first()
        )

        if not tag:
            tag = Tag(name=name, normalized_name=normalized, category=category)
            self.session.add(tag)
            self.session.flush()

        return tag

    def get_or_create_fandom(
        self, name: str, category: Optional[str] = None, estimated_work_count: int = 0
    ) -> Fandom:
        """Get or create a fandom record."""
        normalized = name.lower().strip()

        fandom = (
            self.session.query(Fandom)
            .filter(Fandom.normalized_name == normalized)
            .first()
        )

        if not fandom:
            fandom = Fandom(
                name=name,
                normalized_name=normalized,
                category=category,
                estimated_work_count=estimated_work_count,
            )
            self.session.add(fandom)
            self.session.flush()
        else:
            # Update with latest data
            if category:
                fandom.category = category
            if estimated_work_count > 0:
                fandom.estimated_work_count = estimated_work_count

        return fandom

    def get_or_create_relationship(
        self, name: str, relationship_type: Optional[str] = None
    ) -> Relationship:
        """Get or create a relationship record."""
        normalized = name.lower().strip()

        rel = (
            self.session.query(Relationship)
            .filter(Relationship.normalized_name == normalized)
            .first()
        )

        if not rel:
            rel = Relationship(
                name=name,
                normalized_name=normalized,
                relationship_type=relationship_type,
            )
            self.session.add(rel)
            self.session.flush()

        return rel

    def upsert_work(
        self, scraped: "ScrapedWork", platform: Platform
    ) -> Work:
        """Insert or update a work from scraped data."""
        # Check if work exists
        work = (
            self.session.query(Work)
            .filter(
                Work.platform_id == platform.id,
                Work.platform_work_id == scraped.platform_work_id,
            )
            .first()
        )

        # Handle author
        author_id = None
        if scraped.author:
            author = self.get_or_create_author(
                platform_id=platform.id,
                platform_author_id=scraped.author.platform_author_id,
                username=scraped.author.username,
                display_name=scraped.author.display_name,
                profile_url=scraped.author.profile_url,
                bio=scraped.author.bio,
                patreon_url=scraped.author.patreon_url,
                kofi_url=scraped.author.kofi_url,
            )
            author_id = author.id

        if not work:
            work = Work(
                platform_id=platform.id,
                platform_work_id=scraped.platform_work_id,
                author_id=author_id,
                title=scraped.title,
                summary=scraped.summary,
                url=scraped.url,
                rating=scraped.rating,
                language=scraped.language,
                is_translated=scraped.is_translated,
                original_language=scraped.original_language,
                status=scraped.status,
                chapter_count=scraped.chapter_count,
                word_count=scraped.word_count,
                published_at=scraped.published_at,
                updated_at=scraped.updated_at,
                latest_views=scraped.views,
                latest_likes=scraped.likes,
                latest_comments=scraped.comments,
                latest_bookmarks=scraped.bookmarks,
            )
            self.session.add(work)
            self.session.flush()
        else:
            # Update existing work
            work.author_id = author_id
            work.title = scraped.title
            work.summary = scraped.summary
            work.rating = scraped.rating
            work.language = scraped.language
            work.status = scraped.status
            work.chapter_count = scraped.chapter_count
            work.word_count = scraped.word_count
            work.updated_at = scraped.updated_at
            work.latest_views = scraped.views
            work.latest_likes = scraped.likes
            work.latest_comments = scraped.comments
            work.latest_bookmarks = scraped.bookmarks
            work.scraped_at = datetime.utcnow()

        # Handle tags
        self._sync_work_tags(work, scraped.tags, "freeform")
        self._sync_work_tags(work, scraped.warnings, "warning")

        # Handle fandoms
        self._sync_work_fandoms(work, scraped.fandoms)

        # Handle relationships
        self._sync_work_relationships(work, scraped.relationships)

        return work

    def _sync_work_tags(self, work: Work, tag_names: list[str], category: str) -> None:
        """Sync work tags - add new ones, keep existing."""
        existing_tags = {
            wt.tag.normalized_name for wt in work.tags if wt.tag.category == category
        }

        for i, name in enumerate(tag_names):
            normalized = name.lower().strip()
            if normalized not in existing_tags:
                tag = self.get_or_create_tag(name, category)
                work_tag = WorkTag(work_id=work.id, tag_id=tag.id, is_primary=(i == 0))
                self.session.add(work_tag)

    def _sync_work_fandoms(self, work: Work, fandom_names: list[str]) -> None:
        """Sync work fandoms."""
        existing_fandoms = {wf.fandom.normalized_name for wf in work.fandoms}

        for i, name in enumerate(fandom_names):
            normalized = name.lower().strip()
            if normalized not in existing_fandoms:
                fandom = self.get_or_create_fandom(name)
                work_fandom = WorkFandom(
                    work_id=work.id, fandom_id=fandom.id, is_primary=(i == 0)
                )
                self.session.add(work_fandom)

    def _sync_work_relationships(self, work: Work, relationship_names: list[str]) -> None:
        """Sync work relationships."""
        existing_rels = {wr.relationship.normalized_name for wr in work.relationships}

        for i, name in enumerate(relationship_names):
            normalized = name.lower().strip()
            if normalized not in existing_rels:
                rel = self.get_or_create_relationship(name)
                work_rel = WorkRelationship(
                    work_id=work.id, relationship_id=rel.id, is_primary=(i == 0)
                )
                self.session.add(work_rel)

    def create_engagement_snapshot(self, work: Work) -> EngagementSnapshot:
        """Create a time-series engagement snapshot for a work."""
        snapshot = EngagementSnapshot(
            work_id=work.id,
            snapshot_date=datetime.utcnow(),
            views=work.latest_views,
            likes=work.latest_likes,
            comments=work.latest_comments,
            bookmarks=work.latest_bookmarks,
            chapter_count=work.chapter_count,
            word_count=work.word_count,
        )
        self.session.add(snapshot)
        return snapshot
