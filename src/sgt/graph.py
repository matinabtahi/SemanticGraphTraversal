"""Local RDF loading; retain source membership and parallel predicates."""
from pathlib import Path
from collections import defaultdict
import hashlib
import networkx as nx
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL
from rdflib.compare import to_canonical_graph

SCHEMA_PREDICATES = {RDF.type, RDFS.subClassOf, RDFS.subPropertyOf,
                     RDFS.domain, RDFS.range, OWL.imports, OWL.equivalentClass}


class SemanticGraph:
    def __init__(self):
        self.rdf = Graph()
        self.sources = defaultdict(set)
        self.source_manifest = []

    @classmethod
    def load(cls, paths):
        """Load explicit local Turtle files only; never dereference imports."""
        result = cls()
        for filename in paths:
            path = Path(filename).resolve(strict=True)
            if not path.is_file():
                raise ValueError(f"Not a file: {path}")
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            # Canonicalize and scope blank nodes per source document.
            parsed = to_canonical_graph(Graph().parse(data=data, format="turtle"))
            source = path.as_uri()
            scope = hashlib.sha256(source.encode()).hexdigest()[:16]
            for triple in parsed:
                triple = tuple(BNode(scope + str(t)) if isinstance(t, BNode) else t for t in triple)
                result.rdf.add(triple)
                result.sources[triple].add(source)
            result.source_manifest.append({"source": source, "sha256": digest})
        return result

    def network(self, predicates=None, include_schema=False):
        """Resource-only directed multigraph; literals remain RDF attributes."""
        graph = nx.MultiDiGraph()
        for s, p, o in sorted(self.rdf, key=lambda t: tuple(x.n3() for x in t)):
            graph.add_node(s)
            if isinstance(o, Literal):
                continue
            if predicates is not None and p not in predicates:
                continue
            if not include_schema and p in SCHEMA_PREDICATES:
                continue
            graph.add_edge(s, o, key=p, predicate=p,
                           sources=sorted(self.sources[(s, p, o)]))
        return graph

    def text(self, node):
        """Labels, literal attributes and local type names for retrieval."""
        parts = [str(node).rsplit("#", 1)[-1].rsplit("/", 1)[-1]]
        for p, o in self.rdf.predicate_objects(node):
            if isinstance(o, Literal) or p == RDF.type:
                parts.append(str(o).rsplit("#", 1)[-1])
        return " ".join(sorted(parts))

    def evidence(self, triple, reverse=False):
        s, p, o = triple
        return {"subject": s.n3(), "predicate": str(p), "object": o.n3(),
                "sources": sorted(self.sources[triple]), "traversed_reverse": reverse}
