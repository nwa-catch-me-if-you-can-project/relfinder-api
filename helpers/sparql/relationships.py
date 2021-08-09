from helpers.sparql.query_utils import IRI_PREFIXES
from helpers.sparql.query_utils import (
    uri,
    to_pattern,
    expand_terms
)

from helpers.sparql.structs import (
    QueryCyclesStrategy,
    RelationshipDirection,
    RelationshipQueryConfig
)


def get_queries(query_config: RelationshipQueryConfig):
    """Returns a set of queries to find relations between two objects."""
    queries = {}

    for distance in range(1, query_config.max_distance + 1):
        # get direct connection in both directions
        queries[distance] = []

        direct_query = {
            "query": direct(query_config, distance, RelationshipDirection.FORWARD),
            "src": query_config.entity1IRI,
            "dest": query_config.entity2IRI
        }

        reverse_query = {
            "query": direct(query_config, distance, RelationshipDirection.BACKWARD),
            "src": query_config.entity2IRI,
            "dest": query_config.entity1IRI
        }

        queries[distance].extend([direct_query, reverse_query])

        for a in range(1, distance + 1):
            for b in range(1, distance + 1):
                if ((a + b) == distance):
                    queries[distance].append(middle_object_query(
                        query_config.entity1IRI,
                        query_config.entity2IRI,
                        a,
                        b,
                        to_object=True,
                        query_config=query_config
                    ))

                    queries[distance].append(middle_object_query(
                        query_config.entity1IRI,
                        query_config.entity2IRI,
                        a,
                        b,
                        to_object=False,
                        query_config=query_config
                    ))

    return queries


def direct(query_config, distance, direction=RelationshipDirection.FORWARD):
    """Returns a query for a direct connection between two entities,
    specified in the `query_config` object.

    The `direction` parameter specifies the relationship direction:

    - `FORWARD`: ent1 -> ent2
    - `BACKWARD`: ent2 -> ent1
    """
    if direction == RelationshipDirection.FORWARD:
        entity1IRI, entity2IRI = query_config.entity1IRI, query_config.entity2IRI
    elif direction == RelationshipDirection.BACKWARD:
        entity2IRI, entity1IRI = query_config.entity1IRI, query_config.entity2IRI
    else:
        raise ValueError("Invalid direction parameter")

    variables = {
        "obj": [],
        "pred": []
    }

    if (distance == 1):
        variables["pred"].append("?pf1")

        return complete_query(
            query_config,
            f"{uri(entity1IRI)} ?pf1 {uri(entity2IRI)}",
            variables)
    else:
        query = f"{uri(entity1IRI)} ?pf1 ?of1 .\n"

        variables["pred"].append("?pf1")
        variables["obj"].append("?of1")

        for i in range(1, distance - 1):
            prop, obj1, obj2 = (
                f"?pf{str(i + 1)}",
                f"?of{str(i)}",
                f"?of{str(i + 1)}"
            )
            
            query = f"{query}{obj1} {prop} {obj2}.\n"

            variables["pred"].append(prop)
            variables["obj"].append(obj2)

        # Add the last object to the query
        query = f"{query}?of{str(distance - 1)} ?pf{str(distance)} {uri(entity2IRI)}"

        variables["pred"].append(f"?pf{str(distance)}")

        return complete_query(query_config, query, variables)


def middle_object_query(
        first: str,
        second: str,
        dist1: int,
        dist2: int,
        to_object: bool,
        query_config: RelationshipQueryConfig):
    """Returns a set of queries to find relations between two
    objects, connected by middle objects
    
    - first: first object
    - second: second object
    - dist1/dist2:  distance between the first and second object to the
                    middle. Both have to be greater that 1
    - to_object: arrow direction
    - query_config: RelationshipQueryConfig object

    Patterns:

    if to_object is true then:

    PATTERN												DIST1	DIST2

    first-->?middle<--second 						  	    1		1
    first-->?of1-->?middle<--second						    2		1
    first-->?middle<--?os1<--second 						1		2
    first-->?of1-->middle<--?os1<--second				    2		2
    first-->?of1-->?of2-->middle<--second				    3		1

    if to_object is false then (reverse arrows)

    first<--?middle-->second     
    """
    if dist1 < 1:
        raise ValueError("dist1 must be >= 1")

    if dist2 < 1:
        raise ValueError("dist2 must be >= 1")

    variables = {
        "pred": [],
        "obj": ["?middle"],
    }

    # Generate $first-pf1->of1-pf2->middle
    core_query, first_tmp_vars = generate_middle_object_query(
        core_query="",
        object=first,
        distance=dist1,
        fs="f",
        to_object=to_object
    )

    # Generate $second-ps1->os1-pf2->middle
    core_query, second_tmp_vars = generate_middle_object_query(
        core_query=core_query,
        object=second,
        distance=dist2,
        fs="s",
        to_object=to_object
    )

    variables["pred"].extend(first_tmp_vars["pred"] + second_tmp_vars["pred"])
    variables["obj"].extend(first_tmp_vars["obj"] + second_tmp_vars["obj"])

    return {
        "query": complete_query(query_config, core_query, variables),
        "src": first,
        "dest": second
    }


def generate_middle_object_query(core_query, object, distance, fs, to_object):
    variables = {
        "pred": [],
        "obj": []
    }

    if (distance == 1):
        pattern = to_pattern(
            uri(object),
            f"?p{fs}1",
            "?middle",
            to_object
        )

        core_query = core_query + pattern
        variables["pred"].append(f"?p{fs}1")
    else:
        pattern = to_pattern(
            uri(object),
            f"?p{fs}1",
            f"?o{fs}1",
            to_object
        )

        core_query = core_query + pattern
        variables["pred"].append(f"?p{fs}1")

        for x in range(1, distance):
            subject, prop = f"?o{fs}{x}", f"?p{fs}{x + 1}"

            variables["obj"].append(subject)
            variables["pred"].append(prop)

            if x + 1 == distance:
                core_query = core_query + to_pattern(subject , prop, "?middle", to_object)
            else:
                core_query = core_query + to_pattern(
                    subject,
                    prop,
                    f"?o{fs}{x + 1}",
                    to_object
                )

    return core_query, variables


def generate_filter(query_config, variables: dict):
    """Adds filters for ignored object and properties.
    
    The `variables` dictionary should have the following form:
    
    {
        "pred" ["?pf1", ...],
        "obj" ["?of1", ...]
    }
    """
    filter_terms = []

    for prop in variables["pred"]:
        # Filter out ignored properties
        for ignored_prop in query_config.ignored_properties:
            filter_terms.append(f"{prop} != {uri(ignored_prop)} ")

    for obj in variables["obj"]:
        # Ignore literals
        filter_terms.append(f"!isLiteral({obj})")

        # Filter out ignored objects
        for ignored_obj in query_config.ignored_objects:
            filter_terms.append(f"{obj} != {uri(ignored_obj)} ")

        if query_config.avoid_cycles != QueryCyclesStrategy.NONE:
            # Cycle avoidance
            entity1_uri, entity2_uri = (
                uri(query_config.entity1IRI),
                uri(query_config.entity2IRI)
            )

            filter_terms.append(f"{obj} != {entity1_uri} ")
            filter_terms.append(f"{obj} != {entity2_uri} ")

            if query_config.avoid_cycles == QueryCyclesStrategy.NO_INTERMEDIATE_DUPLICATES:
                for other_obj in variables['obj']:
                    if obj != other_obj:
                        filter_terms.append(f"{obj} != {other_obj} ")

    expanded_terms = expand_terms(filter_terms, "&&")

    return f"FILTER {expanded_terms}. "


def complete_query(query_config, core_query, variables):
    """Adds prefixes and suffixes to a SPARQL query, along
    with the query filters"""
    out_query = '';

    for item in IRI_PREFIXES:
        out_query = f"{out_query}PREFIX {item}: <{IRI_PREFIXES[item]}>\n"

    out_query = f"{out_query}SELECT * WHERE {{\n"
    out_query = f"{out_query}{core_query}\n"
    out_query = f"{out_query}{generate_filter(query_config, variables)}\n}}"

    if query_config.limit is not None:
        out_query = f"{out_query}LIMIT {query_config.limit}"

    return out_query
