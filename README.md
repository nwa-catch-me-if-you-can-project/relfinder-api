# RelFinder API

This repository contains the backend for RelFinder, developed as a `Flask` API.

### Development setup

To run the app in development mode run the following commands

```sh
export FLASK_APP=api
export FLASK_ENV=development
flask run
```

### Production setup

The production app is deployed via docker. To build the docker image execute

```sh
docker build . -t relfinder-api:0.0.1
```

To run the container execute

```sh
docker run --rm -p 5000:5000 relfinder-api:0.0.1
```

### TODOs

* [x] Dockerize app
* [x] Integrate middle object queries
* [x] Check why queries with "xxxx Ivy League men's ...." fail
* [x] Distance option