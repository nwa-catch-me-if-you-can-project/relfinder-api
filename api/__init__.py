import json

from flask import request

from api.app import app

from api.helpers.sparql import add_type_label
from api.helpers.auth import authenticate
from api.helpers import relabel_transactions
from api.helpers.validation import (
    validate_json,
    ValidationSchema
)


@app.route("/")
def index():
    return {
        "message": "ok"
    }


@app.route("/entities")
@authenticate
def entities():
    all_entities = app.sparql.entities()

    return json.dumps({
        "entities": all_entities
    })


@app.route("/triples-count")
@authenticate
def triples_count():
    # FIXME: Check if GUOs affect this
    countries_count = app.sparql.entity_count_for_class("http://w3id.org/um/cbcm/eu-cm-ontology#Country")
    companies_count = app.sparql.entity_count_for_class("http://w3id.org/um/cbcm/eu-cm-ontology#Company")
    persons_count = app.sparql.entity_count_for_class("http://w3id.org/um/cbcm/eu-cm-ontology#Person")

    return json.dumps({
        "count": int(countries_count) + int(companies_count) + int(persons_count)
    })


@app.route("/entities/properties", methods=("POST", ))
@authenticate
@validate_json(schema=ValidationSchema.DATAPROPS)
def dataprops():
    iri = request.json["iri"]
    properties = app.sparql.entity_data_properties(iri)

    return json.dumps({
        "properties": properties
    })


@app.route("/query", methods=("POST", ))
@authenticate
@validate_json(schema=ValidationSchema.QUERY)
def query():
    entities_iris = request.json["entities"]

    (nodes, edges), raw_response = app.sparql.find_relationships(
        entities_iris[0],
        entities_iris[1],
        max_distance=request.json["maxDistance"]
    )

    if app.debug:
        # Log raw and processed responses to files if debugging
        with open("debug/raw-results.json", "w") as raw_results_file:
            raw_results_file.write(json.dumps(raw_response))

        with open("debug/processed-results.json", "w") as processed_results:
            processed_results.write(json.dumps({
                "nodes": nodes,
                "edges": edges
            }))

    # Retrieve rdfs:label instances for all nodes and edges
    add_type_label(
        endpoint=app.sparql,
        nodes=nodes,
        edges=edges,
        chunk_size=50
    )

    relabel_transactions(nodes)
    edges = app.sparql.merge_edge_duplicates(edges)

    # Create a list of classes in the output graph
    class_list = [n["class"] for n in nodes]
    class_list = list(set(class_list))

    return json.dumps({
        "nodes": nodes,
        "edges": edges,
        "classes": class_list
    })


if __name__ == '__main__':
    app.run(debug=True)
