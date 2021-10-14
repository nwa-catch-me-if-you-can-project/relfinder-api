# RelFinder API

Relfinder is a tool for calculating and visualising paths between entities (nodes) in an RDF Knowledge Graph (or SPARQL endpoint). It is based on the original Relfinder tool developed by Philipp Heim, Steffen Lohmann, Timo Stegemann and others. For more information about the tool and its features, please see: http://www.visualdataweb.org/relfinder.php.

The Relfinder source code in this repository is a Python (`Flask`) porting of the backend of the original Relfinder tool which was developed in PHP. We have also developed a front-end for this Flask API here using `Vue.js`: http://github.com/nwa-catch-me-if-you-can-project/relfinder-frontend

#### Motivation for development 
The original Relfinder had a front-end developed with Adobe Flash / Flex and since this technology has been discontinued, there was a need to preserve the useful functionality of this tool for Semantic Web research and the community. Hence the motivation for porting the tool to Python.

### Development setup

To run the app in development mode run the following commands. Before running the app create a `.env` file (the name of this file must strictly be `.env`) as specified in the **production setup** section

```sh
export FLASK_APP=api
export FLASK_ENV=development
flask run
```

### Production setup

Before running the application create a `.env` file (the name of the file must strictly be `.env`) using the template in `example.env`. The template will look like this:

```
SPARQL_ENDPOINT=*** sparql endpoint url ***
SPARQL_USERNAME=*** sparql endpoint username ***
SPARQL_PASSWORD=*** sparql endpoint pwd ***
API_KEY=*** arbitrary api key (this is just to "pair" with the front-end which should specify the same api key in its .env file) ***
DEBUG=TRUE
ONTOLOGY_PREFIX=*** namespace for main ontology or vocabulary used in the graph ***
```

***Note:*** the `SPARQL_ENDPOINT` address should be an external address (e.g. http://dbpedia.org/sparql). If you would like to test locally using `localhost` or another container, you need to ensure the address is visible to this container.

The `API_KEY` variable is arbitrary to connect the backend to the frontend. We recommend generating such a key with a tool such as [this](https://randomkeygen.com/). If you would like to use the RelFinder frontend as well, you also need to configure `VUE_APP_API_KEY` to have the same value as `API_KEY` in the frontend's `.env` file.

Once you have created the `.env` file, build the docker image with:

```sh
docker build . -t relfinder-api:0.0.1
```

To run the container execute

```sh
docker run --rm -p 5000:5000 relfinder-api:0.0.1
```

### License and contributions

The Relfinder API is developed and copyrighted by Kody Moodley and Walter Simoncini, and released under a dual license (see LICENSE.md file in this repository)
Contributions and bug reports are helpful and welcome.
