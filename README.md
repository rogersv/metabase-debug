## First do this

1. Create and activate a venv:
```bash
$ python -m venv venv
$ source venv/bin/activate 
``` 
2. Install packages. If you dont have access to pypi.lime.tech in the venv install limepkg-metabase first:
```bash
$ pip install limepkg-metabase==1.4.0.dev2 --index-url https://pypi.lime.tech/simple/
$ pip install -r requirements.txt
```
3. Get an `.env` from Roger. See below for an example file.
4. Add a session cookie for consul to the `.env` file.

## How to run export test

To create a file with appliction data that can be used for testing export do:

```bash
$ python main.py load-applications -e <ENVIRONMENT>
```

`ENVIRONMENT` can be either `testing` or `production`. Applications will be stored in a file called `application-<ENVIRONMENT>.json`.

To run the export command use

```bash
$ python main.py test-export -e <ENVIRONMENT>
```

This will loop over all applications in the `application-<ENVIRONMENT>.json` and invoke the export API in limepkg-metabase. 

The result of the export will be saved as `export_status` for each application in the file.

## Sample .env file

```yaml
CLOUD_ADMIN_API_KEY = ""
CLOUD_ADMIN_ENDPOINT = ""

# CONSUL
CONSUL_COOKIE_PROD = ""
CONSUL_SERVER_PROD = ""

CONSUL_COOKIE_TESTING = ""
CONSUL_SERVER_TESTING = ""

# Metabase
METABASE_PRODUCTION_ADMIN_USERNAME = ""
METABASE_PRODUCTION_ADMIN_PASSWORD = ""
METABASE_PRODUCTION_METABASE_URL = ""

METABASE_TESTING_ADMIN_USERNAME = ""
METABASE_TESTING_ADMIN_PASSWORD = ""
METABASE_TESTING_METABASE_URL = ""

# LAMBDA LimeBI App Credentials
LAMBDA_PRODUCTION_API_KEY = ""
LAMBDA_PRODUCTION_ENDPOINT = ""
LAMBDA_TESTING_API_KEY = ""
LAMBDA_TESTING_ENDPOINT = ""
```
