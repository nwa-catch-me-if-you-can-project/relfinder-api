import json

from flask import Flask, request
from flask_cors import CORS

from dotenv import load_dotenv

from helpers.sparql import SPARQLEndpoint


app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return open("responses/hello.json").read()


@app.route("/entities")
def entities():
    sparql = SPARQLEndpoint()
    all_entities = sparql.entities()

    return json.dumps({
        "entities": all_entities
    })


@app.route("/triples-count")
def triples_count():
    sparql = SPARQLEndpoint()

    countries_count = sparql.entity_count_for_class("http://w3id.org/um/cbcm/eu-cm-ontology#Country")
    companies_count = sparql.entity_count_for_class("http://w3id.org/um/cbcm/eu-cm-ontology#Company")
    persons_count = sparql.entity_count_for_class("http://w3id.org/um/cbcm/eu-cm-ontology#Person")

    return json.dumps({
        "count": int(countries_count) + int(companies_count) + int(persons_count)
    })


@app.route("/entities/properties", methods=("POST", ))
def dataprops():
    iri = request.json["iri"]

    sparql = SPARQLEndpoint()
    properties = sparql.entity_data_properties(iri)

    return json.dumps({
        "properties": properties
    })


@app.route("/query", methods=("POST", ))
def query():
    entities_iris = request.json["entities"]

    graph = json.loads(
        open("responses/graph.json").read()
    )

    nodes = graph["nodes"]
    edges = graph["edges"]

    selected_nodes = [n for n in nodes if n["iri"] in entities_iris]
    selected_nodes_ids = [n["id"] for n in selected_nodes]

    selected_edges = [
        e for e in edges if
        e["sid"] in selected_nodes_ids and
        e["tid"] in selected_nodes_ids
    ]

    selected_classes = [
        n["class"] for n in selected_nodes
    ]

    return json.dumps({
        "nodes": selected_nodes,
        "edges": selected_edges,
        "classes": selected_classes
    })


if __name__ == '__main__':
    app.run(debug=True)
