from helpers import chunks


def add_type_label(
        endpoint,
        nodes: list,
        edges: list,
        chunk_size: int = 50):
    # Extract IRIs
    props = [e["iri"] for e in edges]
    objects = [o["iri"] for o in nodes]

    # Chunk requests to avoid dbpedia limits
    chunked_labels_entities = chunks(props + objects, chunk_size)
    chunked_type_entities = chunks(objects, chunk_size)

    labels_map, types_map = {}, {}

    for chunk in chunked_labels_entities:
        labels_map = {
            **labels_map,
            **endpoint.label_for_entities(chunk)
        }

    for chunk in chunked_type_entities:
        types_map = {
            **types_map,
            **endpoint.type_for_entities(chunk)
        }

    # Add label and type information
    for node in nodes:
        if node["iri"] in labels_map:
            node["label"] = labels_map[node["iri"]]

        if node["iri"] in types_map:
            node["class"] = types_map[node["iri"]]
        else:
            node["class"] = "Thing"

    for edge in edges:
        if edge["iri"] in labels_map:
            edge["label"] = labels_map[edge["iri"]]
