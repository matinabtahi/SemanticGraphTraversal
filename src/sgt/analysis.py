"""Domain reports preserve asserted values and evidence; no causal claims."""
import networkx as nx
from rdflib import URIRef
from rdflib.namespace import RDF
from .namespaces import RC, GM, SGT


def topology(graph, predicates=None):
    net = graph.network(predicates=predicates)
    simple = nx.DiGraph(net)
    return {"resource_nodes": len(net), "resource_edges": net.number_of_edges(),
            "weak_components": nx.number_weakly_connected_components(net),
            "strong_components": nx.number_strongly_connected_components(net),
            "is_directed_acyclic": nx.is_directed_acyclic_graph(simple),
            "degree": {n.n3(): int(d) for n, d in sorted(net.degree, key=lambda x: x[0].n3())},
            "scope": "asserted resource edges, common schema predicates excluded; literals excluded"}


def thermal_model(graph, model):
    model = URIRef(model)
    rdf = graph.rdf
    if (model, RDF.type, RC.RCModel) not in rdf:
        raise ValueError("Expected an explicitly typed rcont:RCModel")
    rows = []
    for relation in (RC.hasResistance, RC.hasCapacitance, RC.hasSolarAperture):
        for parameter in sorted(rdf.objects(model, relation), key=str):
            triples = [(model, relation, parameter)] + list(rdf.triples((parameter, None, None)))
            rows.append({"parameter": parameter.n3(), "kind": str(relation),
                         "values": [v.n3() for v in sorted(rdf.objects(parameter, RC.numericValue), key=str)],
                         "units": sorted(map(str, rdf.objects(parameter, RC.unit))),
                         "evidence": [graph.evidence(t) for t in sorted(triples, key=str)]})
    return {"model": model.n3(), "zones": sorted(map(str, rdf.objects(model, RC.modelsZone))),
            "parameters": rows, "inputs": sorted(map(str, rdf.objects(model, RC.hasInput))),
            "states": sorted(map(str, rdf.objects(model, RC.hasState))),
            "versions": sorted(map(str, rdf.objects(model, RC.hasModelVersion)))}


def lifecycle(graph, entity):
    entity = URIRef(entity)
    rdf = graph.rdf
    relations = [GM.aboutEntity, GM.aboutObject, GM.aboutPerson, GM.aboutOrganization, GM.aboutPlace, GM.aboutEvent]
    records = {s for p in relations for s in rdf.subjects(p, entity)}
    rows = []
    for record in records:
        triples = list(rdf.triples((record, None, None)))
        rows.append({"record": record.n3(),
                     "dates": sorted(map(str, rdf.objects(record, GM.recordDate))),
                     "media": sorted(map(str, rdf.objects(record, GM.hasMedia))),
                     "model_versions": sorted(map(str, rdf.objects(record, SGT.documentsModelVersion))),
                     "previous": sorted(map(str, rdf.objects(record, GM.previousRecord))),
                     "evidence": [graph.evidence(t) for t in sorted(triples, key=str)]})
    rows.sort(key=lambda r: (r["dates"][0] if r["dates"] else "9999", r["record"]))
    chronology = nx.DiGraph()
    chronology.add_nodes_from(records)
    chronology.add_edges_from((s, o) for s in records for o in rdf.objects(s, GM.previousRecord) if o in records)
    return {"entity": entity.n3(), "records": rows,
            "sequence_has_cycle": not nx.is_directed_acyclic_graph(chronology),
            "scope": "asserted subject links; dates order display, previousRecord defines sequence"}
