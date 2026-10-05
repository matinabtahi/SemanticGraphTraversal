from pathlib import Path
import hashlib
import json
import pytest
from rdflib import Graph, Namespace, URIRef, Literal
from pyshacl import validate
from sgt import SemanticGraph, traverse, lifecycle, thermal_model, topology
from sgt.namespaces import RC, GM, SGT
from sgt.cli import main

ROOT = Path(__file__).resolve().parents[1]
EX = Namespace('https://example.org/sgt-demo#')

@pytest.fixture
def graph():
    return SemanticGraph.load([ROOT/'examples/retrofit.ttl'])

def test_bridge_path_and_parameter_value(graph):
    predicates = {SGT.documentsModelVersion, SGT.hasModelSnapshot, RC.hasResistance}
    result = traverse(graph, EX.AfterRecord, direction='out', predicates=predicates,
                      query='insulation thermal resistance', max_depth=3)
    hit = next(r for r in result['results'] if r['node'] == EX.RAfter.n3())
    assert [e['predicate'] for e in hit['path']] == list(map(str, [SGT.documentsModelVersion, SGT.hasModelSnapshot, RC.hasResistance]))
    assert hit['depth'] == 3
    assert all(e['sources'] and not e['traversed_reverse'] for e in hit['path'])
    report = thermal_model(graph, EX.AfterModel)
    assert any('0.0120' in ' '.join(p['values']) for p in report['parameters'])

def test_reverse_keeps_original_assertion(graph):
    result = traverse(graph, EX.RAfter, direction='in', max_depth=1)
    hit = next(r for r in result['results'] if r['node'] == EX.AfterModel.n3())
    assert hit['path'][0]['subject'] == EX.AfterModel.n3()
    assert hit['path'][0]['object'] == EX.RAfter.n3()
    assert hit['path'][0]['traversed_reverse']

def test_cycles_budgets_and_determinism(graph):
    a = traverse(graph, EX.AfterRecord, max_depth=20, max_nodes=3)
    assert a == traverse(graph, EX.AfterRecord, max_depth=20, max_nodes=3)
    assert a['visited_nodes'] == 3 and a['truncated_by_node_budget']
    assert len({r['node'] for r in a['results']}) == 3
    assert traverse(graph, EX.AfterRecord, max_depth=0)['visited_nodes'] == 1

@pytest.mark.parametrize('kwargs', [{'direction':'wrong'}, {'max_depth':-1}, {'max_nodes':0}, {'limit':0}])
def test_invalid_controls(graph, kwargs):
    with pytest.raises(ValueError):
        traverse(graph, EX.AfterRecord, **kwargs)

def test_missing_start(graph):
    with pytest.raises(ValueError):
        traverse(graph, EX.Missing)

def test_parallel_edges_and_literals(graph):
    graph.rdf.add((EX.AfterRecord, GM.relatedRecord, EX.BeforeRecord))
    net = graph.network()
    assert len(net[EX.AfterRecord][EX.BeforeRecord]) == 3
    assert not any(isinstance(n, Literal) for n in net)

def test_lifecycle_and_cycle_detection(graph):
    result = lifecycle(graph, EX.ZoneA)
    assert [r['dates'][0] for r in result['records']] == ['2024-01-10','2025-01-10']
    assert result['records'][1]['model_versions'] == [str(EX.AfterVersion)]
    assert not result['sequence_has_cycle']
    graph.rdf.add((EX.BeforeRecord, GM.previousRecord, EX.AfterRecord))
    assert lifecycle(graph, EX.ZoneA)['sequence_has_cycle']

def test_provenance_duplicate_triples_and_blank_node_scope(tmp_path):
    text = '@prefix ex: <https://example.org/> . ex:a ex:p ex:b . _:x ex:p ex:a .'
    paths = [tmp_path/'one.ttl', tmp_path/'two.ttl']
    for p in paths:
        p.write_text(text)
    graph = SemanticGraph.load(paths)
    assert len(graph.rdf) == 3
    triple = tuple(URIRef('https://example.org/'+n) for n in ['a','p','b'])
    assert len(graph.sources[triple]) == 2
    assert graph.source_manifest[0]['sha256'] == hashlib.sha256(text.encode()).hexdigest()

def test_weak_connector_does_not_prune_relevant_node(graph):
    result = traverse(graph, EX.AfterRecord, query='resistance', max_depth=3,
        direction='out', predicates={SGT.documentsModelVersion, SGT.hasModelSnapshot, RC.hasResistance})
    assert result['results'][0]['node'] == EX.RAfter.n3()

def test_custom_scorer_contract(graph):
    class BadScorer:
        name='broken'
        def score(self, query, texts):
            return [float('nan')]*len(texts)
    with pytest.raises(ValueError):
        traverse(graph, EX.AfterRecord, scorer=BadScorer())

def test_sparql_history(graph):
    rows = list(graph.rdf.query((ROOT/'queries/model-history.rq').read_text()))
    assert len(rows) == 2
    assert float(rows[0].value) == 0.0075
    assert float(rows[1].value) == 0.012

def test_upstream_compatibility_and_negative_shapes(graph):
    ontology = Graph()
    for path in [ROOT/'SGT.ttl',ROOT/'vendor/RCOnt.ttl',ROOT/'vendor/GMOnt.ttl']:
        ontology.parse(path,format='turtle')
    shapes = Graph().parse(ROOT/'shapes/SGT.shacl.ttl',format='turtle')
    assert validate(graph.rdf, shacl_graph=shapes, ont_graph=ontology, inference='rdfs')[0]
    graph.rdf.remove((EX.AfterVersion, SGT.hasModelSnapshot, EX.AfterModel))
    assert not validate(graph.rdf, shacl_graph=shapes, ont_graph=ontology, inference='rdfs')[0]

def test_every_turtle_parses_and_vendor_hashes():
    for path in ROOT.rglob('*.ttl'):
        Graph().parse(path,format='turtle')
    for entry in json.loads((ROOT/'vendor/manifest.json').read_text()):
        assert hashlib.sha256((ROOT/'vendor'/entry['path']).read_bytes()).hexdigest() == entry['sha256']

def test_cli_all_reports(tmp_path):
    for command, start in [('traverse',EX.AfterRecord),('thermal',EX.AfterModel),('lifecycle',EX.ZoneA),('topology',EX.ZoneA)]:
        target = tmp_path/(command+'.json')
        main([command,'--data',str(ROOT/'examples/retrofit.ttl'),'--start',str(start),'--output',str(target)])
        assert json.loads(target.read_text())['sources']

def test_topology_empty():
    result=topology(SemanticGraph())
    assert result['resource_nodes'] == result['weak_components'] == 0
