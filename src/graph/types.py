"""Typed result structures for thinking-tool graph queries."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DocRef:
    """Lightweight reference to a document node."""

    title: str = ""
    path: str = ""
    uid: str = ""
    status: str = ""
    created: str = ""
    confidence: float = 0.0
    claim: str = ""


@dataclass
class EntityPair:
    """A pair of entities that co-occur across documents."""

    entity_a: str
    entity_b: str
    co_occurrence_count: int = 0


@dataclass
class TopicCount:
    """A topic with its document count."""

    topic: str
    count: int = 0


@dataclass
class TagCount:
    """A tag with its document count."""

    tag: str
    count: int = 0


@dataclass
class MonthlyCount:
    """Document count for a single month."""

    month: str  # YYYY-MM
    count: int = 0


@dataclass
class TrendItem:
    """A concept or entity with its mention frequency trend."""

    name: str
    counts: list[MonthlyCount] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Thinking-tool result types
# ---------------------------------------------------------------------------


@dataclass
class ChallengeEvidence:
    """Result of ``bg think challenge``."""

    topic: str = ""
    decisions: list[DocRef] = field(default_factory=list)
    contradictions: list[DocRef] = field(default_factory=list)
    reversed: list[DocRef] = field(default_factory=list)


@dataclass
class EmergenceReport:
    """Result of ``bg think emerge``."""

    period_days: int = 30
    trending_tags: list[TagCount] = field(default_factory=list)
    entity_clusters: list[EntityPair] = field(default_factory=list)
    topic_density: list[TopicCount] = field(default_factory=list)


@dataclass
class ConnectionPaths:
    """Result of ``bg think connect``."""

    concept_a: str = ""
    concept_b: str = ""
    shortest_path: list[str] = field(default_factory=list)
    shared_nodes: list[str] = field(default_factory=list)
    bridging_docs: list[DocRef] = field(default_factory=list)


@dataclass
class GraduateContext:
    """Result of ``bg think graduate``."""

    idea: str = ""
    source_doc: DocRef | None = None
    related_docs: list[DocRef] = field(default_factory=list)
    nearby_projects: list[DocRef] = field(default_factory=list)


@dataclass
class FrequencyTimeline:
    """Result of ``bg think forecast``."""

    topic: str = ""
    monthly_counts: list[MonthlyCount] = field(default_factory=list)
    trend_direction: str = ""  # "rising", "falling", "stable"
    related_trends: list[TrendItem] = field(default_factory=list)


@dataclass
class AuditEvidence:
    """Result of ``bg think audit``."""

    claim: str = ""
    supporting: list[DocRef] = field(default_factory=list)
    contradicting: list[DocRef] = field(default_factory=list)
    unverified: list[DocRef] = field(default_factory=list)
