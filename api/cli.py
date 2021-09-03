# Copyright (C) <2021>  <Kody Moodley and Walter Simoncini>
# License: https://www.gnu.org/licenses/agpl-3.0.txt

"""Command line tools for mock data generation"""
import json
import click
import random
import faker_microservice

from faker import Faker


@click.group()
def cli():
    pass


@cli.command()
def generate_dataprops():
    fakegen = Faker()

    entities_dataprops = []
    entities = json.loads(
        open("responses/entities.json").read()
    )

    for ent in entities:
        entities_dataprops.append({
            "entity": ent["iri"],
            "props": [
                {
                    "iri"  : "http://w3id.org/um/cbcm/eu-cm-ontology#phoneNumber",
                    "label": "Phone number",
                    "value": fakegen.phone_number()
                },
                {
                    "iri"  : "http://w3id.org/um/cbcm/eu-cm-ontology#registrationISO",
                    "label": "Registration Country ISO",
                    "value": fakegen.bank_country()
                },
                {
                    "iri"  : "http://w3id.org/um/cbcm/eu-cm-ontology#hasIBAN",
                    "label": "Bank IBAN",
                    "value": fakegen.iban()
                },
                {
                    "iri"  : "http://w3id.org/um/cbcm/eu-cm-ontology#hasPrimaryOffice",
                    "label": "Primary office address",
                    "value": fakegen.address()
                }
            ]
        })

    with open("responses/dataprop.json", "w") as props_file:
        props_file.write(json.dumps(
            entities_dataprops
        ))


@cli.command()
@click.argument("edges-count", type=int, default=20)
@click.argument("props-count", type=int, default=5)
def generate_graph(edges_count, props_count):
    faker_api = Faker()
    faker_api.add_provider(faker_microservice.Provider)

    properties = [
        {
            "iri": "http://w3id.org/um/cbcm/eu-cm-ontology#" + faker_api.microservice().replace(" ", ""),
            "label": faker_api.bs()
        }
        for _ in range(props_count)
    ]

    entities = json.loads(
        open("responses/entities.json").read()
    )

    for idx, ent in enumerate(entities):
        # Assign IDs to entities
        ent["id"] = idx + 1

    node_ids = list(range(len(entities)))

    # Create unique edges
    edge_set = set()
    final_edges = []

    while len(final_edges) < edges_count:
        prop = random.choice(properties)
        random_edge = {
            "sid": random.choice(node_ids),
            "tid": random.choice(node_ids),
            "_color": "#000000"
        }

        random_edge = {**random_edge, **prop}

        json_edge = json.dumps(random_edge)

        if json_edge not in edge_set:
            edge_set.add(json_edge)
            final_edges.append(random_edge)

    out_graph = {
        "nodes": entities,
        "edges": final_edges
    }

    with open("responses/graph.json", "w") as out_file:
        out_file.write(json.dumps(out_graph))


if __name__ == '__main__':
    cli()
