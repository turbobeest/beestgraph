"""Tests for thinking-tool query builders in src/graph/queries.py."""

from __future__ import annotations

from src.graph.queries import (
    audit_queries,
    challenge_queries,
    connect_queries,
    emerge_queries,
    forecast_queries,
    graduate_queries,
)


class TestChallengeQueries:
    def test_returns_three_named_queries(self) -> None:
        queries = challenge_queries("ai-ml")
        assert len(queries) == 3
        names = [q[0] for q in queries]
        assert names == ["decisions", "contradictions", "reversed"]

    def test_topic_in_params(self) -> None:
        queries = challenge_queries("databases")
        for _name, _cypher, params in queries:
            assert params["topic"] == "databases"

    def test_decisions_query_filters_type(self) -> None:
        queries = challenge_queries("test")
        _, cypher, _ = queries[0]
        assert "decision" in cypher
        assert "adr" in cypher
        assert "journal" in cypher

    def test_contradictions_query_uses_edge(self) -> None:
        queries = challenge_queries("test")
        _, cypher, _ = queries[1]
        assert "CONTRADICTS" in cypher


class TestEmergeQueries:
    def test_returns_three_named_queries(self) -> None:
        queries = emerge_queries(30)
        assert len(queries) == 3
        names = [q[0] for q in queries]
        assert names == ["trending_tags", "entity_clusters", "topic_density"]

    def test_tag_query_orders_by_count(self) -> None:
        queries = emerge_queries()
        _, cypher, _ = queries[0]
        assert "ORDER BY cnt DESC" in cypher

    def test_entity_cluster_threshold(self) -> None:
        queries = emerge_queries()
        _, cypher, _ = queries[1]
        assert "cnt >= 3" in cypher


class TestConnectQueries:
    def test_returns_three_named_queries(self) -> None:
        queries = connect_queries("A", "B")
        assert len(queries) == 3
        names = [q[0] for q in queries]
        assert names == ["shortest_path", "shared_nodes", "bridging_docs"]

    def test_concept_names_in_params(self) -> None:
        queries = connect_queries("FalkorDB", "Neo4j")
        for _name, _cypher, params in queries:
            assert params["a"] == "FalkorDB"
            assert params["b"] == "Neo4j"

    def test_shortest_path_uses_max_depth(self) -> None:
        queries = connect_queries("A", "B")
        _, cypher, _ = queries[0]
        assert "*..5" in cypher


class TestGraduateQueries:
    def test_returns_three_named_queries(self) -> None:
        queries = graduate_queries("my-idea")
        assert len(queries) == 3
        names = [q[0] for q in queries]
        assert names == ["source_doc", "related_docs", "nearby_projects"]

    def test_slug_in_params(self) -> None:
        queries = graduate_queries("20260301")
        for _name, _cypher, params in queries:
            assert params["slug"] == "20260301"

    def test_source_doc_searches_multiple_fields(self) -> None:
        queries = graduate_queries("test")
        _, cypher, _ = queries[0]
        assert "uid" in cypher
        assert "path" in cypher
        assert "title" in cypher


class TestForecastQueries:
    def test_returns_two_named_queries(self) -> None:
        queries = forecast_queries("ai-ml")
        assert len(queries) == 2
        names = [q[0] for q in queries]
        assert names == ["monthly_counts", "related_trends"]

    def test_topic_in_params(self) -> None:
        queries = forecast_queries("science")
        for _name, _cypher, params in queries:
            assert params["topic"] == "science"

    def test_monthly_counts_uses_substring(self) -> None:
        queries = forecast_queries("test")
        _, cypher, _ = queries[0]
        assert "substring" in cypher


class TestAuditQueries:
    def test_returns_three_named_queries(self) -> None:
        queries = audit_queries("FalkorDB is fast")
        assert len(queries) == 3
        names = [q[0] for q in queries]
        assert names == ["matching", "supporting", "contradicting"]

    def test_claim_in_params(self) -> None:
        queries = audit_queries("test claim")
        for _name, _cypher, params in queries:
            assert params["claim"] == "test claim"

    def test_matching_uses_fulltext(self) -> None:
        queries = audit_queries("test")
        _, cypher, _ = queries[0]
        assert "fulltext.queryNodes" in cypher

    def test_supporting_uses_supports_edge(self) -> None:
        queries = audit_queries("test")
        _, cypher, _ = queries[1]
        assert "SUPPORTS" in cypher

    def test_contradicting_uses_contradicts_edge(self) -> None:
        queries = audit_queries("test")
        _, cypher, _ = queries[2]
        assert "CONTRADICTS" in cypher
