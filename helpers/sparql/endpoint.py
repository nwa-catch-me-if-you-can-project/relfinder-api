import os
import json

from pprint import pp

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
        # FIXME: Update allowed classes (or load from config?)
        # allowed_classes = [
        #     "<http://w3id.org/um/cbcm/eu-cm-ontology#Company>",
        #     "<http://w3id.org/um/cbcm/eu-cm-ontology#Person>",
        #     "<http://w3id.org/um/cbcm/eu-cm-ontology#Country>"
        # ]

        allowed_classes = [
            "<http://schema.org/Person>"
        ]

        allowed_classes = ", ".join(allowed_classes)

        query = f"""
            SELECT ?s ?ctype ?label WHERE {{
                ?s a ?ctype ;
                rdfs:label | <http://w3id.org/um/cbcm/eu-cm-ontology#name> ?label .
                FILTER (?ctype IN ({allowed_classes}))
            }} LIMIT 1000
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

    def find_relationships(self, entity1: str, entity2: str, max_distance: int):
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
            max_distance=max_distance
        )

        query_blocks = get_queries(query_config=query_config)
        queries, output_paths = [], []

        for _, block in query_blocks.items():
            queries.extend(block)

        for query in queries:
            self.sparql.setQuery(query["query"])

            results = self.sparql.query().convert()

            output_paths.append({
                "src": query["src"],
                "dest": query["dest"],
                "paths": results['results']['bindings']
            })

        return self.__build_relationships_graph(
            entity1,
            entity2,
            output_paths)

    def __build_relationships_graph(self, src: str, dest: str, path_collections: list):
        nodes = self.__extract_relationship_nodes(
            src=src,
            dest=dest,
            path_collections=path_collections
        )

        edges = self.__extract_relationship_edges(
            src=src,
            dest=dest,
            path_collections=path_collections,
            nodes=nodes
        )

        nodes = [{
            "label": k.split("/")[-1],
            "iri": k,
            "id": nodes[k],
            "class": "MockClass"
        } for k in nodes.keys()]

        return nodes, edges

    def __extract_relationship_nodes(self, src: str, dest: str, path_collections: list):
        node_idx = 2
        nodes = {
            src: 0,
            dest: 1
        }

        for collection in path_collections:
            for path in collection["paths"]:
                # Extract all object keys (ofx) from the path
                obj_keys = [
                    k for k in list(path.keys())
                    if "of" in k
                ]

                for k in obj_keys:
                    # Add the node to the nodes dictionary if
                    # it does not exist yet
                    entity = path[k]["value"]

                    if entity not in nodes:
                        nodes[entity] = node_idx
                        node_idx += 1

        return nodes

    def __extract_relationship_edges(self, src: str, dest: str, path_collections: list, nodes: dict):
        edges = []

        for collection in path_collections:
            for path in collection["paths"]:
                path_components = list(path.keys())

                if len(path_components) == 1:
                    # Direct connection
                    prop = path[
                        path_components[0]
                    ]["value"]

                    edges.append({
                        "sid": src,
                        "tid": dest,
                        "iri": prop,
                        "label": "Lorem dolor"
                    })
                else:
                    # Indirect connection
                    edges.extend(self.__extract_path_edges(
                        nodes[collection["src"]],
                        nodes[collection["dest"]],
                        path,
                        path_components,
                        nodes
                    ))

        # Keep only unique edges
        edges = set([json.dumps(e) for e in edges])
        return [json.loads(e) for e in edges]

    def __extract_path_edges(self, src: str, dest: str, path: list, path_components: list, nodes: dict):
        edges = []

        for idx, k in enumerate(path_components):
            prop = path[k]["value"]

            if "pf" in k:
                # Forward relationship
                prev_idx = idx - 1
                next_idx = idx + 1

                # FIXME: This shit is horrible
                sid = src if prev_idx < 0 else nodes[path[path_components[prev_idx]]["value"]]
                tid = dest if next_idx >= len(path_components) else nodes[path[path_components[next_idx]]["value"]]

                edges.append({
                    "sid": sid,
                    "tid": tid,
                    "iri": prop,
                    "label": "Lorem dolor"
                })
            else:
                # FIXME: missing psx handling
                # Backward relationship
                continue

        return edges
