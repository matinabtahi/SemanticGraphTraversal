# Architecture

## Responsibility boundaries

RCOnt owns thermal-model semantics. GMOnt owns longitudinal record semantics.
SGT supplies traversal, application-level integration and evidence-backed reports.
The traversal engine also accepts RDF without either companion ontology.

| Module | Contract |
| --- | --- |
| graph.py | Local Turtle to RDF, source hashes and a directed resource multigraph |
| traversal.py | Start node, direction, predicate filter and budgets to ranked paths |
| ranking.py | Query and resource descriptions to finite relevance scores |
| analysis.py | RDF to thermal, lifecycle and topology reports |
| cli.py | Command-line arguments to JSON |
| SGT.ttl | Two explicit bridge properties |
| shapes/ | Application-level structural and numeric constraints |

## Traversal policy

The reference project ranks the frontier by embedding similarity. SGT first collects
a bounded neighborhood using breadth-first search, then ranks the collected resources.
This keeps a poorly labelled model version from hiding a relevant downstream parameter.
It is a deliberate algorithmic difference; no comparative performance is claimed.

The traversal validates its controls, expands deterministically ordered edges,
records the first shortest-hop path to each resource, then scores descriptions and
sorts by descending score, ascending depth and identifier. Nodes are visited once.
Alternative equal-length paths are not enumerated. Direction can be out, in or both.
Reverse steps preserve the original triple and set `traversed_reverse=true`.

The depth limit defines scope. The node budget limits admission and sets a truncation
flag when it excludes additional reachable nodes. The result limit only reduces the
returned rows. The seed is a candidate and may appear in ranked results.

## RDF and provenance

RDF identifiers and parallel predicates are preserved. Literal values remain RDF
attributes rather than traversal vertices. Common schema predicates (type, subclass,
subproperty, domain, range, imports and equivalent class) are excluded from traversal.
Other edges, including units and provenance, remain traversable. Explicit predicate
allowlists are recommended for domain-specific questions. Use instance files for
traversal and load schemas separately for validation.

Blank nodes are canonicalized within each source and scoped by source URI. Moving a
file changes those scoped IDs. Canonicalization may be expensive for highly symmetric
blank-node graphs. Repeated triples retain all source memberships. Reports contain
local source paths and byte hashes; consider that before sharing outputs.

## Analysis boundaries

Thermal inspection preserves asserted numeric literals, units and parameter evidence;
it does not perform unit conversion or numerical simulation. Lifecycle reports follow
explicit subject links, sort dates for display and detect previousRecord cycles within
that subject's records. They do not validate cross-subject chronology or causal claims.
Topology reports degree, component counts and acyclicity of resource relationships;
resource subjects with no retained edges remain isolated nodes. These metrics are not
physical RC-network metrics.

SHACL requires linked versions to have one snapshot and checks positive RC parameters
and their endpoints. RDFS inference is enabled during validation only. This is an
application profile, not a complete OWL consistency or physical correctness test.

## Complexity and extension points

Neighborhood traversal is O(V+E), apart from stable sorting and path copying. The
current implementation scans the loaded triples to build the resource graph per
request and stores the dataset in memory. Source canonicalization and embedding costs
are additional. This targets research datasets, not out-of-core graph databases.

Scorers are replaceable. Future extensions could add a separately named semantic
frontier strategy, graph-store adapters, unit-aware model comparison and per-claim
LLM synthesis. Those are proposals, not implemented features. Retrieval-quality claims
require a benchmark with labelled competency questions.
