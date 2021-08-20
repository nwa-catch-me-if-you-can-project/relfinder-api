def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def relabel_transactions(nodes):
    """Given a list of nodes relabels transactions as tx_type#tx_id"""
    label_maps = {
        "http://w3id.org/um/cbcm/eu-cm-ontology#CrossBorderConversion": "CrossBorderConversion",
        "http://w3id.org/um/cbcm/eu-cm-ontology#CrossBorderDivision": "CrossBorderDivision",
        "http://w3id.org/um/cbcm/eu-cm-ontology#CrossBorderMerger": "CrossBorderMerger"
    }

    for node in nodes:
        if node["class"] in label_maps:
            node["label"] = f"{label_maps[node['class']]}#{node['label']}"
