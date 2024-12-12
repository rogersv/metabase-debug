import os
import shutil
import tempfile
from pathlib import Path

import click
from dotenv import load_dotenv
from limepkg_metabase.serialization.file_operations import (
    create_modified_tarball,
    extract_tarball,
)

import util

load_dotenv(override=True)

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

METABASE_LIME_CLOUD_ADMIN_USERNAME = os.getenv(
    "METABASE_LIME_CLOUD_ADMIN_USERNAME"
)
METABASE_LIME_CLOUD_ADMIN_PASSWORD = os.getenv(
    "METABASE_LIME_CLOUD_ADMIN_PASSWORD"
)
METABASE_LIME_CLOUD_METABASE_URL = os.getenv(
    "METABASE_LIME_CLOUD_METABASE_URL"
)

METABASE_LIME_CLOUD_DEV_ADMIN_USERNAME = os.getenv(
    "METABASE_LIME_CLOUD_DEV_ADMIN_USERNAME"
)
METABASE_LIME_CLOUD_DEV_ADMIN_PASSWORD = os.getenv(
    "METABASE_LIME_CLOUD_DEV_ADMIN_PASSWORD"
)
METABASE_LIME_CLOUD_DEV_METABASE_URL = os.getenv(
    "METABASE_LIME_CLOUD_DEV_METABASE_URL"
)

TEST_IMPORT_APP_ID = os.getenv("TEST_IMPORT_APP_ID")
TEST_IMPORT_APP_USERNAME = os.getenv("TEST_IMPORT_APP_USERNAME")
TEST_IMPORT_APP_PASSWORD = os.getenv("TEST_IMPORT_APP_PASSWORD")

LIME_BI_CREDENTIALS = {
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
    "lime_cloud": {
        "admin_username": METABASE_LIME_CLOUD_ADMIN_USERNAME,
        "admin_password": METABASE_LIME_CLOUD_ADMIN_PASSWORD,
        "metabase_url": METABASE_LIME_CLOUD_METABASE_URL,
    },
    "lime_cloud_dev": {
        "admin_username": METABASE_LIME_CLOUD_DEV_ADMIN_USERNAME,
        "admin_password": METABASE_LIME_CLOUD_DEV_ADMIN_PASSWORD,
        "metabase_url": METABASE_LIME_CLOUD_DEV_METABASE_URL,
    },
}


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
    util.test_export_for_apps(LIME_BI_CREDENTIALS, environment)


@click.command()
def import_collection():
    util.import_collection_to_lime_bi(
        app_id="d50c43e32a4447a0be647d3d2079115a",
        app_information={
            "app_user_username": TEST_IMPORT_APP_USERNAME,
            "app_user_password": TEST_IMPORT_APP_PASSWORD,
            "lime_bi_config": {
                "unique_identifier": "roger-test-db-image",
                "group_name": "roger-test-db-image",
                "group_id": 16,
                "database_id": 22,
                "collection_id": 42,
                "is_initialized": True,
            },
        },
        lime_bi_credentials={
            "admin_username": METABASE_LIME_CLOUD_DEV_ADMIN_USERNAME,
            "admin_password": METABASE_LIME_CLOUD_DEV_ADMIN_PASSWORD,
            "metabase_url": METABASE_LIME_CLOUD_DEV_METABASE_URL,
        },
    )


@click.command()
def remove_segments():
    export_tarfile_path = "export.tar.gz"

    with tempfile.TemporaryDirectory():
        temp_dir_database = Path(tempfile.mkdtemp())
        extract_tarball(export_tarfile_path, temp_dir_database)
        util.remove_all_segments_in_files(temp_dir_database)

    new_tarball_path = create_modified_tarball(temp_dir_database)
    shutil.move(new_tarball_path, "modified_export.tar.gz")


@click.command()
def test_replace_segments():

    apps = util.load_application_data("testing")
    source_app_id = "89cc050582504c248364ca7bf0365d00"
    source_database_id = 89
    destination_database_id = 22

    source_app = apps[source_app_id]

    client_factory_old = util.MetabaseCloudClientFactory(
        source_app_id,
        LIME_BI_CREDENTIALS["testing"]["admin_username"],
        LIME_BI_CREDENTIALS["testing"]["admin_password"],
        LIME_BI_CREDENTIALS["testing"]["metabase_url"],
        app_user_username=source_app["app_user_username"],
        app_user_password=source_app["app_user_password"],
    )

    client_factory_new = util.MetabaseCloudClientFactory(
        TEST_IMPORT_APP_ID,
        LIME_BI_CREDENTIALS["lime_cloud_dev"]["admin_username"],
        LIME_BI_CREDENTIALS["lime_cloud_dev"]["admin_password"],
        LIME_BI_CREDENTIALS["lime_cloud_dev"]["metabase_url"],
        app_user_username=TEST_IMPORT_APP_USERNAME,
        app_user_password=TEST_IMPORT_APP_PASSWORD,
    )

    util.replace_segments(
        source_client_factory=client_factory_old,
        destination_client_factory=client_factory_new,
        source_database_id=source_database_id,
        destination_database_id=destination_database_id,
    )


cli.add_command(load_applications)
cli.add_command(test_export)
cli.add_command(import_collection)
cli.add_command(remove_segments)
cli.add_command(test_replace_segments)

if __name__ == "__main__":
    cli()
