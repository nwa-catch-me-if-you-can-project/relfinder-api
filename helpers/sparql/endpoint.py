import os

from SPARQLWrapper import (
    JSON,
    SPARQLWrapper
)

from helpers.sparql.structs import (
    QueryCyclesStrategy,
    RelationshipQueryConfig
)

from helpers.sparql.relationships import get_queries


class SPARQLEndpoint():
    def __init__(self) -> None:
        self.sparql = SPARQLWrapper(
            os.environ["SPARQL_ENDPOINT"]
        )

        self.sparql.setReturnFormat(JSON)

    def entities(self) -> list:
        query = """
            SELECT ?s ?ctype ?label WHERE {
                ?s a ?ctype ;
                rdfs:label | <http://w3id.org/um/cbcm/eu-cm-ontology#name> ?label .
                FILTER (?ctype IN (<http://w3id.org/um/cbcm/eu-cm-ontology#Company>, <http://w3id.org/um/cbcm/eu-cm-ontology#Person>, <http://w3id.org/um/cbcm/eu-cm-ontology#Country>))
            }
        """

        self.sparql.setQuery(query)

        results = self.sparql.query().convert()
        results = results["results"]["bindings"]
        results = [{
            "iri": item["s"]["value"],
            "label": item["label"]["value"],
            "class": item["ctype"]["value"]
        } for item in results]

        return results

    def entity_count_for_class(self, class_iri: str) -> int:
        query = f"""
            SELECT (count(distinct ?ent) AS ?entities)
            WHERE {{ ?ent a <{class_iri}> . }}
        """

        self.sparql.setQuery(query)

        results = self.sparql.query().convert()
        entities_count = results["results"]["bindings"][0]["entities"]["value"]

        return int(entities_count)

    def entity_data_properties(self, entity_iri: str) -> list:
        query = """
            SELECT DISTINCT ?s ?p ?propLabel ?propValue WHERE{
                ?s ?p ?propValue .
                ?p rdfs:label | <http://w3id.org/um/cbcm/eu-cm-ontology#name> ?propLabel .
                FILTER isLiteral(?propValue)
            }
        """

        self.sparql.setQuery(query)

        results = self.sparql.query().convert()
        results = results["results"]["bindings"]
        results = [{
            "iri": item["p"]["value"],
            "label": item["propLabel"]["value"],
            "value": item["propValue"]["value"]
        } for item in results]

        return results

    def find_relationships(self, entity1: str, entity2: str):
        """Returns a dictionary representing the direct and
        deep links between entity1 and entity2
        """
        ignored_properties = [
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
            "http://www.w3.org/2004/02/skos/core#subject"
        ]

        query_config = RelationshipQueryConfig(
            entity1IRI=entity1,
            entity2IRI=entity2,
            ignored_objects=[],
            ignored_properties=ignored_properties,
            avoid_cycles=QueryCyclesStrategy.NONE,
            limit=10,
            max_distance=1
        )

        query_blocks = get_queries(query_config=query_config)
        queries, output_links = [], []

        for _, block in query_blocks.items():
            queries.extend(block)

        for query in queries:
            self.sparql.setQuery(query["query"])

            results = self.sparql.query().convert()

            output_links.append(
                results['results']['bindings']
            )

        return output_links
