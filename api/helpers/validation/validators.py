"""This module contains validation schemas for the API endpoints"""
import os
import json

from enum import Enum

from jsonschema.exceptions import ValidationError
from jsonschema import validate, FormatChecker


class ValidationSchema(Enum):
    QUERY = "query"
    DATAPROPS = "dataprops"

    @classmethod
    def load_schema(cls, schema):
        return json.loads(open(
            ValidationSchema.filename_for_schema(schema)
        ).read())

    @classmethod
    def filename_for_schema(cls, schema):
        filename = {
            ValidationSchema.QUERY: "query.json",
            ValidationSchema.DATAPROPS: "dataprops.json"
        }[schema]

        return os.path.join("api/validation_schemas", filename)

    def validate(self, instance: dict):
        schema = ValidationSchema.load_schema(self)

        try:
            validate(
                instance=instance,
                schema=schema,
                format_checker=FormatChecker()
            )

            return True, None
        except ValidationError as ex:
            return False, ex.message
