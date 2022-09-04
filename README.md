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
   
### Running the test locally

After installing all the requirements you can run

   ```sh
   ENV=test pytest -vv --junitxml=pytest.xml --cov=./ --cov-report=xml --cov-config=.coveragerc --cov-branch tests
   ```
