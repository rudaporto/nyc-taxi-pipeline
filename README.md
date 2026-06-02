# Data Ingestion API

Simple API to ingest NYC Taxi dataset files into S3

## Dependencies

- Python 3.11
- uv
- Docker
- go taskfile

## Install

Use uv to create the venv and install the package for local development:

```sh
task install
```

## Tests

Before running the tests, you need to download the test data:

```sh
task download:testdata
```

And now you can run the tests:

```sh
task test
```
