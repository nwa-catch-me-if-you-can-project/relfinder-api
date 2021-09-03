# Copyright (C) <2021>  <Kody Moodley and Walter Simoncini>
# License: https://www.gnu.org/licenses/agpl-3.0.txt

import os
import json

from flask import request
from functools import wraps


def authenticate(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("Api-Key")

        if api_key != os.environ["API_KEY"]:
            return json.dumps({
                "message": "Invalid API key"
            }), 401

        return f(*args, **kwargs)

    return decorated_function
