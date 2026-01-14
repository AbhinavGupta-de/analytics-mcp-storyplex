"""SQLAlchemy models for Storyplex Analytics.

Designed for comprehensive analytics across multiple fanfiction/web novel platforms.
Supports time-series engagement tracking and cross-platform normalization.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class PlatformType(PyEnum):
    """Supported platforms for scraping."""

    AO3 = "ao3"
    FANFICTION_NET = "ffn"
    WATTPAD = "wattpad"
    ROYAL_ROAD = "royalroad"
    WEBNOVEL = "webnovel"
    SCRIBBLE_HUB = "scribblehub"
    SYOSETU = "syosetu"
    MANGADEX = "mangadex"
    WEBTOON = "webtoon"
    TAPAS = "tapas"


class ContentRating(PyEnum):
    """Content rating categories (normalized across platforms)."""

    GENERAL = "general"
    TEEN = "teen"
    MATURE = "mature"
    EXPLICIT = "explicit"
    NOT_RATED = "not_rated"


class WorkStatus(PyEnum):
    """Work completion status."""

    ONGOING = "ongoing"
    COMPLETED = "completed"
    HIATUS = "hiatus"
    ABANDONED = "abandoned"
    UNKNOWN = "unknown"


class Platform(Base):
    """Platform metadata and scraping configuration."""

    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    platform_type: Mapped[PlatformType] = mapped_column(
        Enum(PlatformType), unique=True, nullable=False
    )
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    rate_limit_rps: Mapped[float] = mapped_column(Float, default=1.0)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    authors: Mapped[list["Author"]] = relationship(back_populates="platform")
    works: Mapped[list["Work"]] = relationship(back_populates="platform")


class Author(Base):
    """Author/creator information."""

    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), nullable=False)
    platform_author_id: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    profile_url: Mapped[Optional[str]] = mapped_column(String(512))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    joined_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    work_count: Mapped[int] = mapped_column(Integer, default=0)

    # External monetization links (if discoverable)
    patreon_url: Mapped[Optional[str]] = mapped_column(String(512))
    kofi_url: Mapped[Optional[str]] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    platform: Mapped["Platform"] = relationship(back_populates="authors")
    works: Mapped[list["Work"]] = relationship(back_populates="author")

    __table_args__ = (
        UniqueConstraint("platform_id", "platform_author_id", name="uq_author_platform"),
        Index("ix_author_username", "username"),
    )


class Work(Base):
    """Core work/story entity."""

    __tablename__ = "works"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform_id: Mapped[int] = mapped_column(ForeignKey("platforms.id"), nullable=False)
    platform_work_id: Mapped[str] = mapped_column(String(255), nullable=False)
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("authors.id"))

    # Core metadata
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(512), nullable=False)

    # Content classification
    rating: Mapped[ContentRating] = mapped_column(
        Enum(ContentRating), default=ContentRating.NOT_RATED
    )
    language: Mapped[str] = mapped_column(String(50), default="English")
    is_translated: Mapped[bool] = mapped_column(Boolean, default=False)
    original_language: Mapped[Optional[str]] = mapped_column(String(50))

    # Structure metrics
    status: Mapped[WorkStatus] = mapped_column(Enum(WorkStatus), default=WorkStatus.UNKNOWN)
    chapter_count: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Latest engagement snapshot (denormalized for quick queries)
    latest_views: Mapped[int] = mapped_column(BigInteger, default=0)
    latest_likes: Mapped[int] = mapped_column(BigInteger, default=0)  # kudos, votes, etc.
    latest_comments: Mapped[int] = mapped_column(Integer, default=0)
    latest_bookmarks: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    platform: Mapped["Platform"] = relationship(back_populates="works")
    author: Mapped[Optional["Author"]] = relationship(back_populates="works")
    tags: Mapped[list["WorkTag"]] = relationship(back_populates="work", cascade="all, delete-orphan")
    fandoms: Mapped[list["WorkFandom"]] = relationship(
        back_populates="work", cascade="all, delete-orphan"
    )
    relationships: Mapped[list["WorkRelationship"]] = relationship(
        back_populates="work", cascade="all, delete-orphan"
    )
    engagement_snapshots: Mapped[list["EngagementSnapshot"]] = relationship(
        back_populates="work", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("platform_id", "platform_work_id", name="uq_work_platform"),
        Index("ix_work_title", "title"),
        Index("ix_work_published", "published_at"),
        Index("ix_work_word_count", "word_count"),
        Index("ix_work_views", "latest_views"),
    )


class Tag(Base):
    """Normalized tag/genre entity."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))  # genre, trope, warning, etc.

    # For cross-platform normalization
    canonical_tag_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tags.id"))

    __table_args__ = (
        Index("ix_tag_normalized", "normalized_name"),
        UniqueConstraint("name", "category", name="uq_tag_name_category"),
    )


class WorkTag(Base):
    """Many-to-many relationship between works and tags."""

    __tablename__ = "work_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    work: Mapped["Work"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship()

    __table_args__ = (UniqueConstraint("work_id", "tag_id", name="uq_work_tag"),)


class Fandom(Base):
    """Fandom/source material entity."""

    __tablename__ = "fandoms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))  # anime, books, games, etc.
    parent_fandom_id: Mapped[Optional[int]] = mapped_column(ForeignKey("fandoms.id"))

    # Estimated size metrics
    estimated_work_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (Index("ix_fandom_normalized", "normalized_name"),)


class WorkFandom(Base):
    """Many-to-many relationship between works and fandoms."""

    __tablename__ = "work_fandoms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    fandom_id: Mapped[int] = mapped_column(ForeignKey("fandoms.id"), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    work: Mapped["Work"] = relationship(back_populates="fandoms")
    fandom: Mapped["Fandom"] = relationship()

    __table_args__ = (UniqueConstraint("work_id", "fandom_id", name="uq_work_fandom"),)


class Relationship(Base):
    """Character relationship/pairing entity."""

    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False)
    relationship_type: Mapped[Optional[str]] = mapped_column(String(50))  # romantic, platonic, etc.
    characters: Mapped[Optional[str]] = mapped_column(Text)  # JSON array of character names

    __table_args__ = (Index("ix_relationship_normalized", "normalized_name"),)


class WorkRelationship(Base):
    """Many-to-many relationship between works and character relationships."""

    __tablename__ = "work_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    relationship_id: Mapped[int] = mapped_column(ForeignKey("relationships.id"), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    work: Mapped["Work"] = relationship(back_populates="relationships")
    relationship: Mapped["Relationship"] = relationship()

    __table_args__ = (UniqueConstraint("work_id", "relationship_id", name="uq_work_relationship"),)


class EngagementSnapshot(Base):
    """Time-series engagement data for trend analysis."""

    __tablename__ = "engagement_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Engagement metrics at this point in time
    views: Mapped[int] = mapped_column(BigInteger, default=0)
    likes: Mapped[int] = mapped_column(BigInteger, default=0)  # kudos, votes
    comments: Mapped[int] = mapped_column(Integer, default=0)
    bookmarks: Mapped[int] = mapped_column(Integer, default=0)
    subscribers: Mapped[int] = mapped_column(Integer, default=0)  # followers

    # Structure at snapshot time
    chapter_count: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    work: Mapped["Work"] = relationship(back_populates="engagement_snapshots")

    __table_args__ = (
        UniqueConstraint("work_id", "snapshot_date", name="uq_engagement_snapshot"),
        Index("ix_engagement_date", "snapshot_date"),
    )
