"""``bg think`` command group — structured thinking tools backed by FalkorDB."""

from __future__ import annotations

import json
from typing import Any

from falkordb import FalkorDB

from src.config import load_settings
from src.graph.queries import NamedQuery


def _execute_queries(queries: list[NamedQuery]) -> dict[str, list[list[Any]]]:
    """Execute a list of named queries against the live graph.

    Returns a dict mapping query name to its result_set rows.
    On connection failure, returns empty lists for all queries.
    """
    settings = load_settings()
    try:
        db = FalkorDB(
            host=settings.falkordb.host,
            port=settings.falkordb.port,
            password=settings.falkordb.password or None,
        )
        graph = db.select_graph(settings.falkordb.graph_name)
    except Exception:
        return {name: [] for name, _, _ in queries}

    results: dict[str, list[list[Any]]] = {}
    for name, cypher, params in queries:
        try:
            r = graph.query(cypher, params)
            results[name] = r.result_set if r.result_set else []
        except Exception:
            results[name] = []
    return results


def _format_json(data: Any) -> str:
    """Serialize a dataclass or dict to indented JSON."""
    from dataclasses import asdict

    obj = asdict(data) if hasattr(data, "__dataclass_fields__") else data
    return json.dumps(obj, indent=2, default=str)
