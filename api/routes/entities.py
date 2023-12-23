import dataclasses
from flask import jsonify, Flask

from typing import Any
from doc_store import disk_store


@dataclasses.dataclass
class ContentSummaryResponse:
    hash: str
    summary: str | None

    # @property requires custom logic to support jsonify, don't care for now
    hasSummary: bool

    @classmethod
    def for_hash_response(
        cls, hash: str, summary: str | None, **kwargs
    ) -> "ContentSummaryResponse":
        has_summary = kwargs.pop("has_summary", summary is not None)
        return cls(hash, summary, has_summary, **kwargs)


@dataclasses.dataclass
class GraphNode:
    key: str
    attributes: dict[str, Any] = dataclasses.field(
        default_factory=lambda: {
            "x": 0.0,
            "y": 0.0,
        }
    )


@dataclasses.dataclass
class GraphEdge:
    source: str
    target: str
    relation: str


@dataclasses.dataclass
class Graph:
    nodes: list[GraphNode] = dataclasses.field(default_factory=list)
    edges: list[GraphEdge] = dataclasses.field(default_factory=list)

    def for_node(self, key: str) -> GraphNode:
        node = next(iter(self.nodes), None)
        if not node:
            node = GraphNode(key=key)
            self.nodes.append(node)

        return node


def register_routes(app: Flask):
    @app.get("/entities/<hash>")
    def get_entities(hash: str):
        store = disk_store.default_store()
        entity_relations = store.load_entity_relations(hash)
        return jsonify([x.model_dump() for x in entity_relations])

