import json

from flask import request
from functools import wraps

from .validators import ValidationSchema


def validate_json(schema: ValidationSchema):
    def validate_json_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            is_valid, validation_error = schema.validate(
                request.json
            )

            if not is_valid:
                return json.dumps({
                    "message": validation_error
                }), 400

            return f(*args, **kwargs)

        return decorated_function

    return validate_json_decorator
