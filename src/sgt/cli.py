import argparse
import json
from pathlib import Path
from rdflib import URIRef
from . import SemanticGraph, traverse, topology, thermal_model, lifecycle
from .ranking import SentenceTransformerScorer


def main(argv=None):
    parser = argparse.ArgumentParser(description="Traverse and analyse local RDF Turtle graphs")
    parser.add_argument("command", choices=["traverse", "topology", "thermal", "lifecycle"])
    parser.add_argument("--data", nargs="+", required=True, help="Local Turtle files")
    parser.add_argument("--start", help="Full resource IRI")
    parser.add_argument("--query", default="")
    parser.add_argument("--direction", choices=["out", "in", "both"], default="both")
    parser.add_argument("--predicate", action="append", help="Repeatable full predicate IRI filter")
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--max-nodes", type=int, default=1000)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--embedding-model", help="Opt-in sentence-transformers model or local model path")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.command != "topology" and not args.start:
        parser.error("--start is required for this command")
    try:
        graph = SemanticGraph.load(args.data)
        predicates = set(map(URIRef, args.predicate)) if args.predicate else None
        if args.command == "traverse":
            scorer = SentenceTransformerScorer(args.embedding_model) if args.embedding_model else None
            result = traverse(graph, args.start, query=args.query, direction=args.direction,
                              predicates=predicates, max_depth=args.max_depth,
                              max_nodes=args.max_nodes, limit=args.limit, scorer=scorer)
        elif args.command == "topology":
            result = topology(graph, predicates)
        elif args.command == "thermal":
            result = thermal_model(graph, args.start)
        else:
            result = lifecycle(graph, args.start)
        result.setdefault("sources", graph.source_manifest)
        text = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
