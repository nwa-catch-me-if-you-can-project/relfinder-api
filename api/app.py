# Copyright (C) <2021>  <Kody Moodley and Walter Simoncini>
# License: https://www.gnu.org/licenses/agpl-3.0.txt

import os
import json

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from api.helpers.sparql.endpoint import SPARQLEndpoint


load_dotenv()

app = Flask(__name__)
CORS(app)

app.debug = os.environ.get("DEBUG", False)
os.makedirs("debug", exist_ok=True)

try:
    config = json.loads(open("config.json").read())
    sparql = SPARQLEndpoint(
        allowed_object_properties=config["allowed_object_properties"],
        allowed_entity_classes=config["allowed_entity_classes"]
    )

    app.sparql = sparql
except FileNotFoundError:
    raise FileNotFoundError("config.json not found")
