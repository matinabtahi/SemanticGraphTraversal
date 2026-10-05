# Attribution and reference

The conceptual reference is Daniel Verdejo's
[semantic-graph-traversal-and-analysis](https://github.com/Verdagio/semantic-graph-traversal-and-analysis),
reviewed at commit `5b829f983fcb66cdde3443515e27110b52f99f67`.
It demonstrates embedding-guided exploration followed by LLM analysis.

SGT is an independent implementation. No code from that project is included. SGT uses
bounded RDF neighborhood collection followed by optional semantic ranking, preserves
predicate-level evidence, and supplies RCOnt/GMOnt domain reports. It does not reproduce
the reference algorithm or claim comparative performance.

The vendor directory contains Matin Abtahi's MIT-licensed RCOnt and GMOnt ontology
snapshots for offline compatibility tests. See vendor/manifest.json and vendor/LICENSE.
