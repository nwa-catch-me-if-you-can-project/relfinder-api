from enum import Enum


class QueryCyclesStrategy(Enum):
    """Strategy used to handle cycles in queries.
    
    - NONE:                         No cycle avoidance
    - NO_INTERMEDIATE_OBJECT:       No intermediate object can be object1 or object2
    - NO_INTERMEDIATE_DUPLICATES:   An object can not occur more than once in a connection
    """
    NONE = 0
    NO_INTERMEDIATE_OBJECT = 1
    NO_INTERMEDIATE_DUPLICATES = 2


class RelationshipDirection(Enum):
    FORWARD = 0,
    BACKWARD = 1


class RelationshipQueryConfig():
    """Configuration used to generate relationship queries
    between two objects.

    This class is a simple data object and its properties
    represent:

    - entity1IRI:           the first object
    - entity2IRI:           the second object
    - ignored_objects:      objects which should not be part of
                            the returned connections between the
                            first and second object.
    - ignored_properties:   properties which should not be part
                            of the returned connections between
                            the first and second object.
    - avoid_cycles:         cycle avoidance strategy
    - limit:                maximum number of results per SPARQL query
    - max_distance:         the maximum search distance
    """
    def __init__(
            self,
            entity1IRI: str,
            entity2IRI: str,
            ignored_objects=[],
            ignored_properties=[],
            avoid_cycles=QueryCyclesStrategy.NONE,
            max_distance: int = 4) -> None:
        self.entity1IRI = entity1IRI
        self.entity2IRI = entity2IRI
        self.ignored_objects = ignored_objects
        self.ignored_properties = ignored_properties
        self.avoid_cycles = avoid_cycles
        self.max_distance = max_distance
