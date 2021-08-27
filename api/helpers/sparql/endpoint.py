import os
import json

from SPARQLWrapper import (
    JSON,
    DIGEST,
    SPARQLWrapper
)

from api.helpers.sparql.structs import (
    QueryCyclesStrategy,
    RelationshipQueryConfig
)

from api.helpers.sparql.relationships import get_queries


class SPARQLEndpoint():
    def __init__(
            self,
            allowed_object_properties: list,
            allowed_entity_classes: list) -> None:
        self.allowed_object_properties = allowed_object_properties
        self.allowed_entity_classes = [
            f"<{iri}>" for iri in allowed_entity_classes
        ]

        self.sparql = SPARQLWrapper(
            os.environ["SPARQL_ENDPOINT"]
        )

        self.sparql.setHTTPAuth(DIGEST)
        self.sparql.setCredentials(
            os.environ["SPARQL_USERNAME"],
            os.environ["SPARQL_PASSWORD"]
        )

        # Use reasoning
        self.sparql.addParameter("reasoning", "false")
        self.sparql.setReturnFormat(JSON)

    def entities(self) -> list:
        # FIXME: Load allowed classes from a config file?
        allowed_classes = ", ".join(self.allowed_entity_classes)

        query = f"""
            SELECT ?s ?ctype ?label WHERE {{
                ?s a ?ctype ;
                rdfs:label | <http://w3id.org/um/cbcm/eu-cm-ontology#name> ?label .
                FILTER (?ctype IN ({allowed_classes}))
            }}
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

    def entity_data_properties(self, entity_iri: str, limit: int = 50) -> list:
        query = f"""
            SELECT DISTINCT ?p ?propLabel ?propValue WHERE {{
                <{entity_iri}> ?p ?propValue .
                ?p rdfs:label | <http://w3id.org/um/cbcm/eu-cm-ontology#name> ?propLabel .
                FILTER isLiteral(?propValue)
            }} LIMIT {limit}
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

    def label_for_entities(self, entityIRIs: list):
        entityIRIs = [
            f"{{ ?p rdfs:label | <http://w3id.org/um/cbcm/eu-cm-ontology#name> ?label FILTER(?p = <{iri}>)}}"
            for iri in entityIRIs
        ]

        entitySubqueries = " UNION\n\t\t".join(entityIRIs)

        query = f"""
            SELECT * WHERE {{
                {entitySubqueries}
                FILTER (lang(?label) = 'en' || lang(?label) = '')
            }}
        """

        self.sparql.setQuery(query)

        results = self.sparql.query().convert()["results"]["bindings"]

        # Create a dictionary mapping IRIs to rdfs:label values
        labels_map = {}
        
        for res in results:
            labels_map[res["p"]["value"]] = res["label"]["value"]

        return labels_map

    def type_for_entities(self, entity_iris: list, ontology_prefix: str):
        entity_iris = [
            f"{{ ?o rdf:type ?type FILTER(?o = <{iri}> && !isBlank(?type))}}"
            for iri in entity_iris
        ]

        entity_iris = " UNION\n\t\t".join(entity_iris)

        query = f"""
            SELECT * WHERE {{
                {entity_iris}
            }}
        """

        self.sparql.setQuery(query)
        results = self.sparql.query().convert()["results"]["bindings"]

        # Create a dictionary mapping IRIs to rdf:type values
        type_map = {}

        # If multiple classes are returned for the same entity
        # this selects the last one. Since the SPARQL endpoint
        # returns classes in hierarchical order this results
        # in the most specific class being used.
        #
        # This applies to the CbCM GraphDB endpoint. Your
        # mileage may vary
        for res in results:
            if res["type"]["value"].startswith(ontology_prefix):
                # Only types from the source ontology will be considered
                type_map[res["o"]["value"]] = res["type"]["value"]

        return type_map

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
            avoid_cycles=QueryCyclesStrategy.NO_INTERMEDIATE_DUPLICATES,
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

        if os.environ.get("DEBUG", False):
            with open("debug/queries.json", "w") as queries_file:
                queries_file.write(json.dumps(queries))

        return self._build_relationships_graph(
            entity1,
            entity2,
            output_paths), output_paths

    def _build_relationships_graph(self, src: str, dest: str, path_collections: list):
        nodes = self.__extract_relationship_nodes(
            src=src,
            dest=dest,
            path_collections=path_collections
        )

        edges = self.__extract_relationship_edges(
            path_collections=path_collections,
            nodes=nodes
        )

        nodes = [{
            "label": k.split("/")[-1],
            "iri": k,
            "id": nodes[k],
            "class": "MockClass",
            "isEndpoint": k in [src, dest]
        } for k in nodes.keys()]

        return nodes, edges

    def merge_edge_duplicates(self, edges: list, label_sep="|"):
        """
            Given a list of edges (x --> y) merges duplicates in a
            single edge with multiple property labels
        """
        edges_dict = {}

        for edge in edges:
            key = f"{edge['sid']}-{edge['tid']}"

            if key in edges_dict and edge["label"] not in edges_dict[key]["label"]:
                edges_dict[key]["iris"].append(edge["iri"])
                edges_dict[key]["label"].append(edge["label"])
            else:
                edges_dict[key] = {
                    "sid": edge["sid"],
                    "tid": edge["tid"],
                    "iris": [edge["iri"]],
                    "label": [edge["label"]]
                }

        for _, edge in edges_dict.items():
            # Merge the labels list to a string
            edge["label"] = f" {label_sep} ".join(edge["label"])

        return [v for _, v in edges_dict.items()]

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
                    if self.__is_path_object(k)
                ]

                for k in obj_keys:
                    # Add the node to the nodes dictionary if
                    # it does not exist yet
                    entity = path[k]["value"]

                    if entity not in nodes:
                        nodes[entity] = node_idx
                        node_idx += 1

        return nodes

    def __is_path_object(self, key):
        """Returns whether a SPARQL query element is an object"""
        return "of" in key or "middle" in key or "os" in key

    def __extract_relationship_edges(self, path_collections: list, nodes: dict):
        edges = []

        for collection in path_collections:
            for path in collection["paths"]:
                path_components = list(path.keys())

                if len(path_components) == 1:
                    # Direct connection
                    prop = path[
                        path_components[0]
                    ]["value"]

                    if prop not in self.allowed_object_properties:
                        # Skip non-allowed properties
                        continue

                    edges.append({
                        "sid": nodes[collection["src"]],
                        "tid": nodes[collection["dest"]],
                        "iri": prop,
                        "label": prop.split("/")[-1]
                    })
                else:
                    # Make sure all the properties are in the
                    # allowed object properties list
                    if not self.__is_prop_chain_valid(path):
                        continue

                    # Indirect connection
                    edges.extend(self.__extract_path_edges(
                        collection["src"],
                        collection["dest"],
                        path,
                        path_components,
                        nodes
                    ))

        # Keep only unique edges
        edges = set([json.dumps(e) for e in edges])
        return [json.loads(e) for e in edges]

    def __is_prop_chain_valid(self, path):
        """
            This method verifies that all properties of a path
            are in the allowed_object_properties list
        """
        property_iris = [
            path[k]["value"] for k in list(path.keys())
            if k.startswith("pf") or k.startswith("ps")
        ]

        valid_iris = [
            iri for iri in property_iris
            if iri in self.allowed_object_properties
        ]

        return len(valid_iris) == len(property_iris)

    def __extract_path_edges(self, src: str, dest: str, path: list, path_components: list, nodes: dict):
        forward_props = [k for k in list(path.keys()) if k.startswith("pf")]
        forward_props = sorted(forward_props)

        backward_props = [k for k in list(path.keys()) if k.startswith("ps")]
        backward_props = sorted(backward_props)

        # Forward links
        forward_edges = self.__path_to_edges(
            src=src,
            dest=dest,
            props=forward_props,
            path=path,
            nodes=nodes,
            object_key_prefix="of"
        )

        backward_edges = self.__path_to_edges(
            src=dest,
            dest=src,
            props=backward_props,
            path=path,
            nodes=nodes,
            object_key_prefix="os"
        )

        return forward_edges + backward_edges

    def __path_to_edges(
            self,
            src: str,
            dest: str,
            props: list,
            path: list,
            nodes: dict,
            object_key_prefix="of"):
        """Extracts edges from a given path.
        
        `object_key_prefix` controls whether the direction should be
        forward (of) or backward (os).
        
        current_pos = src
        object_key_prefix = 'of'

        for each prop:
            Does ofx exist? If yes link, pos = ofx
            elif: middle exists? Connect to middle and terminate
            else: connect to dest and terminate
        """
        edges = []
        current_pos = src

        for idx, prop in enumerate(props):
            target_obj = f"{object_key_prefix}{idx + 1}"

            if target_obj in path.keys():
                obj = path[target_obj]["value"]

                edges.append({
                    "sid": nodes[obj],
                    "tid": nodes[current_pos],
                    "iri": path[prop]["value"],
                    "label": path[prop]["value"].split("/")[-1]
                })

                current_pos = obj
            elif "middle" in path.keys():
                e_src, e_dest = nodes[path["middle"]["value"]], nodes[current_pos]

                edges.append({
                    "sid": e_src,
                    "tid": e_dest,
                    "iri": path[prop]["value"],
                    "label": path[prop]["value"].split("/")[-1]
                })

                # No more forward connections after middle
                break
            else:
                # Link to the destination
                edges.append({
                    "sid": nodes[current_pos],
                    "tid": nodes[dest],
                    "iri": path[prop]["value"],
                    "label": path[prop]["value"].split("/")[-1]
                })

        return edges
