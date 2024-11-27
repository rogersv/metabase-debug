Create a venv and run `pip install -r requirements.txt`

Create a .env in the root with:

```
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

Usage:

* `python main.py load-applications -e testing` - creates a json-file with the applications for testing-environment
* `python main.py load-applications -e production`  - same as previous but for production
* `python main.py test-export -e testing` - uses the application file when the test is run. The result of the test is added to the same file, e.g., `"export_status": "failed"`. If there is already an export_status, the app is ignored the next time an export is performed. If you want to run it again, you need to remove the "export_status" line. The same applies to `private_collection_export_status`.
* `python main.py test-export -e production`  - same as previous but for production
