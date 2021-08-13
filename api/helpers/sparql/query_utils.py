IRI_PREFIXES = {
    "cbcm": "http://w3id.org/um/cbcm/eu-cm-ontology#",
    "db" : "http://dbpedia.org/resource/",
    "rdf" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs" : "http://www.w3.org/2000/01/rdf-schema#"
}


def uri(iri, prefixes=IRI_PREFIXES):
    """Prefixes an IRI according to the prefixes map or adds <>

    For an IRI this function:

    1. If the IRI can be prefixed, prefixes it and returns
    2. If the IRI is already prefixes the IRI is returned
    3. Puts brackets around an IRI, e.g. <iri>
    """
    for item in list(prefixes.keys()):
        if iri.startswith(prefixes[item]):
            iri = iri.replace(
                prefixes[item],
                f"{str(item)}:"
            )

            return iri

    if ":" in iri:
        check = iri[:iri.find(':')]

        if check in prefixes:
            return iri

    return f"<{iri}>"


def to_pattern(q_subject, q_property, q_object, to_object):
    """Helper function to generate ?s ?p ?o and ?o ?p ?s triples"""
    if to_object:
        return f"{q_subject} {q_property} {q_object} . \n"

    return f"{q_object} {q_property} {q_subject} . \n"


def expand_terms(terms, operator="&&"):
    """Given a list of terms produces a string in the
    format ((term1) && (term2) && ...) where "&&" is
    the `operator` parameter"""
    result = ""

    for x in range(0, len(terms)):
        result = f"{result}({terms[x]})"

        if ((x + 1) == len(terms)):
            result = result + ""
        else:
            result = result + " " + operator + " "

        result = result + "\n"

    return f"({result})"
