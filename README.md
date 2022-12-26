# Cataloger Python Engine

<!-- ABOUT THE PROJECT -->

## About The Project

### Installation

1. Clone the repo
   ```sh
   git@github.com:squallium/cataloger-python-engine.git
   ```
2. Install poetry following https://python-poetry.org/docs/#installation
3. Install the requirements
   ```sh
   poetry install
   ```

### Features

## Lazy coders

### Lazy mongoose

These scripts will generated based on mongoose scheme the mongoose models and also added the needed connections to work
directly into the express cataloger project

## Templates

### Microservice

Using cookiecutter I've created a template for new microservice to avoid doing manually
   ```sh
   rm -rf <path-to-cataloger>/backend/<microservice-name> && cookiecutter templates/backend-project -o <path-to-cataloger>/backend/
   ```

### Running the test locally

After installing all the requirements you can run

   ```sh
   ENV=test pytest -vv --junitxml=pytest.xml --cov=./ --cov-report=xml --cov-config=.coveragerc --cov-branch tests
   ```

### Tools ###

* Changelog generation ([auto changelog](https://github.com/KeNaCo/auto-changelog))

### Problems ###

* With the auto-changelog library I got
  this ([markupsafe error](https://stackoverflow.com/questions/72191560/importerror-cannot-import-name-soft-unicode-from-markupsafe))
* Semantic release problem with version from
  tag ([bumping version with tag](https://github.com/relekang/python-semantic-release/issues/104))