import json
import logging
import os
import tarfile
from pathlib import Path

import requests
from dotenv import load_dotenv
from limepkg_metabase.api_client import MetabaseClient, MetabaseClientFactory
from limepkg_metabase.authentication.credentials import CloudCredentials
from limepkg_metabase.serialization import (export_collection,
                                            export_personal_collections)

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
        self.credentials = CloudCredentials(app_identifier, self.secrets_path, None)

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
    with export_collection(
        client_factory=client_factory,
        collection_id=app_information["lime_bi_config"]["collection_id"],
        database_id=app_information["lime_bi_config"]["database_id"],
    ) as tarball:
        source = Path(tarball)
        dest = Path(COLLECTION_FILE_NAME)
        dest.write_bytes(source.read_bytes())

    return validate_export_file(app_id, COLLECTION_FILE_NAME)


def export_personal_collections_from_lime_bi(
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

    with export_personal_collections(
        client_factory=client_factory,
        group_id=app_information["lime_bi_config"]["group_id"],
        database_id=app_information["lime_bi_config"]["database_id"],
    ) as tarball:
        source = Path(tarball)
        dest = Path(PERSONAL_COLLECTION_FILE_NAME)
        dest.write_bytes(source.read_bytes())

    return validate_export_file(app_id, PERSONAL_COLLECTION_FILE_NAME)


def validate_export_file(app_id: str, tar_file: str):
    global export_result
    with tarfile.open(tar_file, "r") as tar:
        tar.extractall(path="extracted_files")

    # Look for export.log and scan for the text "Failed"
    log_file_path = Path("extracted_files/lime_bi_collections/export.log")
    if log_file_path.exists():
        with log_file_path.open("r") as log_file:
            failed = False
            for line in log_file:
                if "Failed" in line:
                    failed = True
                    break
            if failed:
                return "failed"
            else:
                return "succeeded"
    else:
        return "failed"

    # shutil.rmtree('extracted_files')


def get_applications_from_cloud_admin(
    lambda_credentials: dict, environment: str = "testing"
):
    apps = load_application_data(environment)

    cloud_admin_client = CloudAdminClient(CLOUD_ADMIN_API_KEY, CLOUD_ADMIN_ENDPOINT)
    found_apps = cloud_admin_client.get_all_docker_swarm_applications(environment)
    for found_app in found_apps:
        identifier = found_app["identifier"]

        if identifier not in apps:
            apps[identifier] = {}

        lime_bi_config = None

        if "lime_bi_config" not in apps[identifier]:
            lime_bi_config = fetch_lime_bi_config(identifier, environment, found_app)

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
        return get_lime_bi_config(identifier)


def fetch_app_user(lambda_credentials, identifier):
    url = f"{lambda_credentials['endpoint']}?app_id={identifier}"
    response = requests.get(
        url,
        headers={"x-api-key": lambda_credentials["api_key"]},
    )
    return json.loads(response.text)


def test_export_for_apps(lime_bi_credentials: dict, environment: str = "testing"):
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
                        app_id, application, lime_bi_credentials
                    )
                    apps[app_id]["export_status"] = result
                except Exception as e:
                    logger.exception(e)
                    apps[app_id]["export_status"] = "failed"
            else:
                apps[app_id]["export_status"] = "failed"

        if "private_collection_export_status" not in application:
            if (
                apps[app_id]["lime_bi_config"] != "Missing"
                and apps[app_id]["app_user_username"] != "Missing"
            ):
                print(app_id)
                try:
                    result = export_personal_collections_from_lime_bi(
                        app_id, application, lime_bi_credentials
                    )
                    apps[app_id]["private_collection_export_status"] = result
                except Exception as e:
                    logger.exception(e)
                    apps[app_id]["private_collection_export_status"] = "failed"
            else:
                apps[app_id]["private_collection_export_status"] = "failed"

        save_application_data(apps, environment)


def get_lime_bi_config(docker_swarm_application_id: str, environment="testing"):
    if environment == "testing":
        consul_client = ConsulClient(CONSUL_COOKIE_TESTING, CONSUL_SERVER_TESTING)
    elif environment == "production":
        consul_client = ConsulClient(CONSUL_COOKIE_PROD, CONSUL_SERVER_PROD)
    else:
        raise Exception(f"Invalid environment: {environment}")

    swarm_config = consul_client.get_application_config(docker_swarm_application_id)
    config = swarm_config.get("config", {})
    if not config:
        return {}
    return config.get("lime-bi", {})
