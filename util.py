import json
import logging
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from limepkg_metabase.api_client import MetabaseClient, MetabaseClientFactory
from limepkg_metabase.authentication.credentials import CloudCredentials
from limepkg_metabase.errors import ExportError
from limepkg_metabase.segments.segment_mapper import SegmentMapper
from limepkg_metabase.serialization import (
    export_all_collections,
    import_all_collections,
)

from cloudadmin import CloudAdminClient
from consul import ConsulClient

logger = logging.getLogger(__name__)
export_result = {"failed": [], "succeeded": []}

load_dotenv()

# CONSUL
CONSUL_COOKIE_PROD = os.getenv("CONSUL_COOKIE_PROD")
CONSUL_SERVER_PROD = os.getenv("CONSUL_SERVER_PROD")

CONSUL_COOKIE_TESTING = os.getenv("CONSUL_COOKIE_TESTING")
CONSUL_SERVER_TESTING = os.getenv("CONSUL_SERVER_TESTING")

# Cloud Admin
CLOUD_ADMIN_API_KEY = os.getenv("CLOUD_ADMIN_API_KEY")
CLOUD_ADMIN_ENDPOINT = os.getenv("CLOUD_ADMIN_ENDPOINT")

COLLECTION_FILE_NAME = "./export.tar.gz"
PERSONAL_COLLECTION_FILE_NAME = "./personal_collections.tar.gz"


class MetabaseCloudClientFactory(MetabaseClientFactory):
    def __init__(
        self,
        app_identifier: str,
        admin_username: str,
        admin_password: str,
        metabase_url: str,
        timeout=None,
        app_user_username=None,
        app_user_password=None,
    ):
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.metabase_url = metabase_url
        self.timeout = timeout
        self.app_user_username = app_user_username
        self.app_user_password = app_user_password
        self.secrets_path = "/run/secrets/"
        self.credentials = CloudCredentials(
            app_identifier, self.secrets_path, None
        )

    def create_admin_client(self):
        return MetabaseClient(
            self.admin_username,
            self.admin_password,
            self.metabase_url,
            self.timeout,
        )

    def create_app_user_client(self):
        return MetabaseClient(
            self.app_user_username,
            self.app_user_password,
            self.metabase_url,
            self.timeout,
        )


def load_application_data(environment: str = "testing"):
    try:
        with open(f"applications-{environment}.json", "r") as file:
            applications = json.load(file)
    except FileNotFoundError:
        applications = {}
        with open(f"applications-{environment}.json", "w") as file:
            json.dump(applications, file)
    return applications


def save_application_data(applications, environment: str = "testing"):
    with open(f"applications-{environment}.json", "w") as file:
        json.dump(applications, file)


def import_collection_to_lime_bi(
    app_id: str, app_information: dict, lime_bi_credentials: dict
):
    client_factory = MetabaseCloudClientFactory(
        app_id,
        lime_bi_credentials["admin_username"],
        lime_bi_credentials["admin_password"],
        lime_bi_credentials["metabase_url"],
        app_user_username=app_information["app_user_username"],
        app_user_password=app_information["app_user_password"],
    )

    # create clients for debug purpose
    admin_client = client_factory.create_admin_client()
    user_client = client_factory.create_app_user_client()

    logger.info(
        "Importing Lime BI collections"
        f" using metabase_url: {client_factory.metabase_url}"
        f" and admin_username: {admin_client.username}"
        f" and admin metabase_url: {admin_client.metabase_url}"
        f" and app_user_username: {user_client.username}"
        f" and app_user metabase_url: {user_client.metabase_url}"
    )
    try:
        widgets = import_all_collections(
            client_factory=client_factory,
            collection_id=app_information["lime_bi_config"]["collection_id"],
            group_id=app_information["lime_bi_config"]["group_id"],
            database_id=app_information["lime_bi_config"]["database_id"],
            tarball_path=COLLECTION_FILE_NAME,
            app_identifier=app_id,
        )
        print(widgets)
    except ExportError as e:
        logger.exception(e)
        return "failed"


def export_collection_from_lime_bi(
    app_id: str, app_information: dict, lime_bi_credentials: dict
):
    client_factory = MetabaseCloudClientFactory(
        app_identifier=app_id,
        admin_username=lime_bi_credentials["admin_username"],
        admin_password=lime_bi_credentials["admin_password"],
        metabase_url=lime_bi_credentials["metabase_url"],
        app_user_username=app_information["app_user_username"],
        app_user_password=app_information["app_user_password"],
    )

    # create clients for debug purpose
    admin_client = client_factory.create_admin_client()
    user_client = client_factory.create_app_user_client()

    logger.info(
        "Exporting Lime BI collections"
        f" using metabase_url: {client_factory.metabase_url}"
        f" and admin_username: {admin_client.username}"
        f" and admin metabase_url: {admin_client.metabase_url}"
        f" and app_user_username: {user_client.username}"
        f" and app_user metabase_url: {user_client.metabase_url}"
    )
    try:
        with export_all_collections(
            client_factory=client_factory,
            collection_id=app_information["lime_bi_config"]["collection_id"],
            group_id=app_information["lime_bi_config"]["group_id"],
            database_id=app_information["lime_bi_config"]["database_id"],
        ) as tarball:
            source = Path(tarball)
            dest = Path(COLLECTION_FILE_NAME)
            dest.write_bytes(source.read_bytes())
            return "succeeded"
    except ExportError as e:
        logger.exception(e)
        return "failed"


def get_applications_from_cloud_admin(
    lambda_credentials: dict, environment: str = "testing"
):
    apps = load_application_data(environment)

    cloud_admin_client = CloudAdminClient(
        CLOUD_ADMIN_API_KEY, CLOUD_ADMIN_ENDPOINT
    )
    found_apps = cloud_admin_client.get_all_docker_swarm_applications(
        environment
    )
    for found_app in found_apps:
        identifier = found_app["identifier"]

        if identifier not in apps:
            apps[identifier] = {}

        lime_bi_config = None

        if "lime_bi_config" not in apps[identifier]:
            lime_bi_config = fetch_lime_bi_config(
                identifier, environment, found_app
            )

            if lime_bi_config:
                apps[identifier]["lime_bi_config"] = lime_bi_config
            else:
                apps[identifier]["lime_bi_config"] = "Missing"

        if "lime_bi_config" in apps[identifier]:
            if "app_user_username" not in apps[identifier]:
                app_user = fetch_app_user(lambda_credentials, identifier)
                try:
                    apps[identifier]["app_user_username"] = app_user[
                        "app_user_username"
                    ]
                    apps[identifier]["app_user_password"] = app_user[
                        "app_user_password"
                    ]
                except Exception:
                    apps[identifier]["app_user_username"] = "Missing"
                    apps[identifier]["app_user_password"] = "Missing"

    save_application_data(apps, environment)


def fetch_lime_bi_config(identifier, environment, found_app):
    if environment == "testing":
        try:
            return json.loads(found_app["lime_bi_config"])
        except Exception:
            return "Missing"
    else:
        return get_lime_bi_config(identifier, environment)


def fetch_app_user(lambda_credentials, identifier):
    url = f"{lambda_credentials['endpoint']}?app_id={identifier}"
    response = requests.get(
        url,
        headers={"x-api-key": lambda_credentials["api_key"]},
    )
    return json.loads(response.text)


def test_export_for_apps(
    lime_bi_credentials: dict, environment: str = "testing"
):
    apps = load_application_data(environment)

    for app_id, application in apps.items():
        if "export_status" not in application:
            if (
                apps[app_id]["lime_bi_config"] != "Missing"
                and apps[app_id]["app_user_username"] != "Missing"
            ):
                print(app_id)
                try:
                    result = export_collection_from_lime_bi(
                        app_id, application, lime_bi_credentials[environment]
                    )
                    apps[app_id]["export_status"] = result
                except Exception as e:
                    logger.exception(e)
                    apps[app_id]["export_status"] = "failed"
            else:
                apps[app_id]["export_status"] = "failed"

        save_application_data(apps, environment)


def get_lime_bi_config(
    docker_swarm_application_id: str, environment="testing"
):
    if environment == "testing":
        consul_client = ConsulClient(
            CONSUL_COOKIE_TESTING, CONSUL_SERVER_TESTING
        )
    elif environment == "production":
        consul_client = ConsulClient(CONSUL_COOKIE_PROD, CONSUL_SERVER_PROD)
    else:
        raise Exception(f"Invalid environment: {environment}")

    swarm_config = consul_client.get_application_config(
        docker_swarm_application_id
    )
    config = swarm_config.get("config", {})
    if not config:
        return {}
    return config.get("lime-bi", {})


def remove_all_segments_in_files(temp_dir):
    file_path = f"{temp_dir}/lime_bi_collections/"
    for root, _, files in os.walk(file_path):
        for file in files:
            if file.endswith(".yaml") or file.endswith(".yml"):
                full_path = os.path.join(root, file)
                print(full_path)
                with open(full_path, "r") as f:
                    content = f.read()
                    content = content.replace("- =", '- "="')
                    modified_content = remove_segment_filters(content)
                with open(full_path, "w") as f:
                    f.write(modified_content)


def remove_segment_filters(yaml_content):
    pattern = r"^\s*- - segment\n(?:^\s+- .+\n)*"

    # Remove the matched filters
    modified_text = re.sub(pattern, "", yaml_content, flags=re.MULTILINE)

    return modified_text


def replace_segments(
    source_client_factory: MetabaseClientFactory,
    destination_client_factory: MetabaseClientFactory,
    source_database_id,
    destination_database_id,
    export_tarfile_path="export.tar.gz",
):

    database_segment_mapper = SegmentMapper(
        source_client_factory=source_client_factory,
        destination_client_factory=destination_client_factory,
        source_database_id=source_database_id,
        destination_database_id=destination_database_id,
    )

    database_segment_mapper.replace_segment_ids_in_tarfile(export_tarfile_path)


def get_table_metadata(user_client, env):
    file_path = f"database-metadata-tables-{env}.json"

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            all_tables = json.load(file)
    else:
        all_tables = user_client.get_tables()
        with open(file_path, "w") as file:
            json.dump(all_tables, file)

    return all_tables


def get_database_metadata(user_client: MetabaseClient, database_id):

    tables = user_client.get_tables()

    database_metadata = {
        "table_ids": [],
        "tables": {},
    }

    for table in tables:
        # make sure it is the correct database_id
        if table["db_id"] == database_id:
            database_metadata["table_ids"].append(table["id"])
            if table["id"] not in database_metadata["tables"]:
                database_metadata["tables"][table["id"]] = {
                    "table_info": {},
                    "segments": {},
                }
            database_metadata["tables"][table["id"]]["table_info"] = table

    all_segments = user_client.get_segments()
    for segment in all_segments:
        if segment["table_id"] in database_metadata["table_ids"]:
            database_metadata["tables"][segment["table_id"]]["segments"][
                segment["description"]
            ] = segment

    for table in tables:
        if not table["id"] in database_metadata["tables"]:
            continue
        if not database_metadata["tables"][table["id"]]["segments"]:
            del database_metadata["tables"][table["id"]]

    return database_metadata
