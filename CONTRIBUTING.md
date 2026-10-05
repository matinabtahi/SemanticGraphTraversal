# Contributing

Open an issue describing the modelling or retrieval problem before proposing a large change.
Use focused pull requests and include tests for changed traversal or semantic behaviour.

```bash
python -m pip install -r requirements.txt
python -m pytest
```

Preserve the established RCOnt and GMOnt namespaces. Propose domain vocabulary changes
in the relevant upstream repository; keep this repository's bridge small. Never silently
replace asserted triples with inferred relations. Every retrieval result must preserve
its source and traversal direction. Document scorer identity and limitations.

Update CHANGELOG.md and documentation with public API changes. The project uses semantic
versioning; the 0.x series is experimental. Do not commit credentials, personal datasets,
generated reports, model weights or virtual environments. Synthetic examples should be
clearly labelled. Upstream snapshots must retain their licence and commit provenance.
