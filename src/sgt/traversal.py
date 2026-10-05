"""Bounded traversal with deterministic shortest evidence paths and ranking."""
from collections import deque
import math
from rdflib import URIRef
from .ranking import LexicalScorer


def traverse(graph, start, *, query="", direction="both", predicates=None,
             max_depth=4, max_nodes=1000, limit=20, scorer=None):
    """Collect a bounded neighborhood, then rank it without pruning connectors.

    Shortest paths refer to hop count in the selected resource graph. Incoming
    traversal records its direction; it never asserts a new inverse RDF triple.
    """
    if direction not in {"out", "in", "both"}:
        raise ValueError("direction must be out, in or both")
    if max_depth < 0 or max_nodes < 1 or limit < 1:
        raise ValueError("depth must be nonnegative; node budget and limit must be positive")
    network = graph.network(predicates=predicates)
    start = URIRef(start) if isinstance(start, str) else start
    if start not in network:
        raise ValueError(f"Unknown start node: {start}")
    paths = {start: []}
    queue = deque([start])
    truncated = False
    while queue:
        node = queue.popleft()
        if len(paths[node]) >= max_depth:
            continue
        edges = []
        if direction in {"out", "both"}:
            edges += [(v, (u, p, v), False) for u, v, p in network.out_edges(node, keys=True)]
        if direction in {"in", "both"}:
            edges += [(u, (u, p, v), True) for u, v, p in network.in_edges(node, keys=True)]
        for neighbor, triple, reverse in sorted(edges, key=lambda e: (e[0].n3(), tuple(t.n3() for t in e[1]), e[2])):
            if neighbor in paths:
                continue
            if len(paths) >= max_nodes:
                truncated = True
                continue
            paths[neighbor] = paths[node] + [graph.evidence(triple, reverse)]
            queue.append(neighbor)
    nodes = sorted(paths, key=lambda n: n.n3())
    scorer = scorer or LexicalScorer()
    scores = scorer.score(query, [graph.text(n) for n in nodes])
    if len(scores) != len(nodes) or any(not math.isfinite(float(s)) for s in scores):
        raise ValueError("Scorer must return one finite score per candidate")
    rows = [{"node": n.n3(), "score": float(score), "depth": len(paths[n]),
             "text": graph.text(n), "path": paths[n]} for n, score in zip(nodes, scores)]
    rows.sort(key=lambda row: (-row["score"], row["depth"], row["node"]))
    return {"start": start.n3(), "query": query, "direction": direction,
            "max_depth": max_depth, "max_nodes": max_nodes,
            "predicates": sorted(map(str, predicates)) if predicates is not None else None,
            "scorer": scorer.name, "inference": "none", "visited_nodes": len(nodes),
            "truncated_by_node_budget": truncated, "returned_nodes": min(limit, len(rows)),
            "sources": graph.source_manifest, "results": rows[:limit]}
