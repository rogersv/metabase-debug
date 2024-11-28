import os

import click
from dotenv import load_dotenv

import util

load_dotenv()

LAMBDA_PRODUCTION_API_KEY = os.getenv("LAMBDA_PRODUCTION_API_KEY")
LAMBDA_PRODUCTION_ENDPOINT = os.getenv("LAMBDA_PRODUCTION_ENDPOINT")
LAMBDA_TESTING_API_KEY = os.getenv("LAMBDA_TESTING_API_KEY")
LAMBDA_TESTING_ENDPOINT = os.getenv("LAMBDA_TESTING_ENDPOINT")

METABASE_PRODUCTION_ADMIN_USERNAME = os.getenv(
    "METABASE_PRODUCTION_ADMIN_USERNAME"
)
METABASE_PRODUCTION_ADMIN_PASSWORD = os.getenv(
    "METABASE_PRODUCTION_ADMIN_PASSWORD"
)
METABASE_PRODUCTION_METABASE_URL = os.getenv(
    "METABASE_PRODUCTION_METABASE_URL"
)

METABASE_TESTING_ADMIN_USERNAME = os.getenv("METABASE_TESTING_ADMIN_USERNAME")
METABASE_TESTING_ADMIN_PASSWORD = os.getenv("METABASE_TESTING_ADMIN_PASSWORD")
METABASE_TESTING_METABASE_URL = os.getenv("METABASE_TESTING_METABASE_URL")

METABASE_LIME_CLOUD_ADMIN_USERNAME = os.getenv("METABASE_LIME_CLOUD_ADMIN_USERNAME")
METABASE_LIME_CLOUD_ADMIN_PASSWORD = os.getenv("METABASE_LIME_CLOUD_ADMIN_PASSWORD")
METABASE_LIME_CLOUD_METABASE_URL = os.getenv("METABASE_LIME_CLOUD_METABASE_URL")

TEST_IMPORT_APP_USERNAME = os.getenv("TEST_IMPORT_APP_USERNAME")
TEST_IMPORT_APP_PASSWORD = os.getenv("TEST_IMPORT_APP_PASSWORD")


@click.group()
def cli():
    pass


@click.command()
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["production", "testing"]),
    required=True,
    help="The environment to use (production or testing)",
)
def load_applications(environment):
    lambda_credentials = {
        "production": {
            "api_key": LAMBDA_PRODUCTION_API_KEY,
            "endpoint": LAMBDA_PRODUCTION_ENDPOINT,
        },
        "testing": {
            "api_key": LAMBDA_TESTING_API_KEY,
            "endpoint": LAMBDA_TESTING_ENDPOINT,
        },
    }
    util.get_applications_from_cloud_admin(
        lambda_credentials[environment], environment
    )


@click.command()
@click.option(
    "--environment",
    "-e",
    type=click.Choice(["production", "testing"]),
    required=True,
    help="The environment to use (production or testing)",
)
def test_export(environment):
    lime_bi_credentials = {
        "production": {
            "admin_username": METABASE_PRODUCTION_ADMIN_USERNAME,
            "admin_password": METABASE_PRODUCTION_ADMIN_PASSWORD,
            "metabase_url": METABASE_PRODUCTION_METABASE_URL,
        },
        "testing": {
            "admin_username": METABASE_TESTING_ADMIN_USERNAME,
            "admin_password": METABASE_TESTING_ADMIN_PASSWORD,
            "metabase_url": METABASE_TESTING_METABASE_URL,
        },
    }
    util.test_export_for_apps(lime_bi_credentials[environment], environment)


@click.command()
def import_collection():
    util.import_collection_to_lime_bi(
        app_id="0b6ea78da60d4aae817a13c304ac4fb5",
        app_information={
            "app_user_username": TEST_IMPORT_APP_USERNAME,
            "app_user_password": TEST_IMPORT_APP_PASSWORD,
            "lime_bi_config": {
                "unique_identifier": "corem-test",
                "group_name": "corem-test",
                "group_id": 62,
                "database_id": 60,
                "collection_id": 291,
                "is_initialized": True
            },
        },
        lime_bi_credentials={
            "admin_username": METABASE_LIME_CLOUD_ADMIN_USERNAME,
            "admin_password": METABASE_LIME_CLOUD_ADMIN_PASSWORD,
            "metabase_url": METABASE_LIME_CLOUD_METABASE_URL,
        },
    )


cli.add_command(load_applications)
cli.add_command(test_export)
cli.add_command(import_collection)

if __name__ == "__main__":
    cli()
