import json

from flask import Flask, request
from flask_cors import CORS

from dotenv import load_dotenv

from helpers.sparql.endpoint import SPARQLEndpoint
from helpers.sparql import add_type_label

load_dotenv()

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

    endpoint = SPARQLEndpoint()
    nodes, edges = endpoint.find_relationships(
        entities_iris[0],
        entities_iris[1],
        max_distance=request.json["maxDistance"]
    )

    # Retrieve rdfs:label instances for all nodes and edges
    add_type_label(
        endpoint=endpoint,
        nodes=nodes,
        edges=edges,
        chunk_size=50
    )

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
