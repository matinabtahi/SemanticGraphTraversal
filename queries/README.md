# Query catalogue

model-history.rq returns subjects, dated records, versions, snapshots and resistance
values with units. It runs on asserted triples and returns two rows on the example.
The query supports aboutEntity/aboutObject subject links; extend its alternatives for
other GMOnt subject types if required.

```python
from pathlib import Path
from rdflib import Graph

graph = Graph().parse('examples/retrofit.ttl', format='turtle')
for row in graph.query(Path('queries/model-history.rq').read_text()):
    print(row)
```
