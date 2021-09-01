# RelFinder API

This repository contains the backend for RelFinder, developed as a `Flask` API.

### Development setup

To run the app in development mode run the following commands. Before running the app create a `.env` file as specified in the **production setup** section

```sh
export FLASK_APP=api
export FLASK_ENV=development
flask run
```

### Production setup

Before running the application create a `.env` file using the template in `example.env`. The `API_KEY` variable is arbitrary, we recommend generating one with a tool such as [this](https://randomkeygen.com/). If you are using the RelFinder frontend, you also need to configure `VUE_APP_API_KEY` to have the same value as `API_KEY` in the frontend's `.env` file.

Once you created the `.env` file, build the docker image with:

```sh
docker build . -t relfinder-api:0.0.1
```

To run the container execute

```sh
docker run --rm -p 5000:5000 relfinder-api:0.0.1
```