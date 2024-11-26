import json

import requests


class CloudAdminClient:
    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key
        self.domain = domain

    def get_application_uid_by_subdomain(
        self,
        app_subdomain: str,
        cloud_domain: str = "internal-dev.limecrm.cloud",
    ) -> str:

        url = f"{self.domain}/api/v1/query/"
        query = {
            "limetype": "application",
            "responseFormat": {
                "object": {
                    "_id": None,
                    "uid": None,
                }
            },
            "filter": {
                "key": "url",
                "op": "=",
                "exp": f"{app_subdomain}.{cloud_domain}",
            },  # noqa
        }
        params = "q=" + json.dumps(query)
        headers = {
            "x-api-key": self.api_key,
            "accept": "application/hal+json",
        }
        response = requests.get(url=url, headers=headers, params=params)
        result = json.loads(response.text)
        if len(result["objects"]) != 1:
            raise Exception("Only application should be found")

        return result["objects"][0].get("uid")

    def get_application_uid_by_docker_swarm_id(self, docker_swarm_id: str) -> str:

        url = f"{self.domain}/api/v1/query/"
        query = {
            "limetype": "application",
            "responseFormat": {
                "object": {
                    "_id": None,
                    "uid": None,
                }
            },
            "filter": {
                "key": "docker_swarm._id",
                "op": "=",
                "exp": docker_swarm_id,
            },  # noqa
        }
        params = "q=" + json.dumps(query)
        headers = {
            "x-api-key": self.api_key,
            "accept": "application/hal+json",
        }
        response = requests.get(url=url, headers=headers, params=params)
        result = json.loads(response.text)

        if len(result["objects"]) != 1:
            raise Exception("Only application should be found")

        return result["objects"][0].get("uid")

    def get_all_docker_swarm_applications(self, environment: str = "testing") -> str:

        url = f"{self.domain}/api/v1/query/"
        query = {
            "limetype": "docker_swarm",
            "responseFormat": {
                "object": {
                    "_id": None,
                    "identifier": None,
                    "lime_bi_config": None,
                }
            },
            "filter": {
                "op": "AND",
                "exp": [
                    {"key": "lime_bi_active", "op": "=", "exp": True},
                ],
            },
            "limit": 0,  # noqa
        }

        if environment == "testing":
            query["filter"]["exp"].append(
                {"key": "swarm_environment", "op": "=", "exp": "testing"}
            )
        else:
            query["filter"]["exp"].append(
                {"key": "lime_bi_production", "op": "!=", "exp": "testing"}
            )

        params = "q=" + json.dumps(query)
        headers = {
            "x-api-key": self.api_key,
            "accept": "application/hal+json",
        }
        response = requests.get(url=url, headers=headers, params=params)
        result = json.loads(response.text)

        return result["objects"]

    def create_docker_swarm_object(self, data: dict):
        headers = {
            "x-api-key": self.api_key,
            "accept": "application/hal+json",
        }
        url = f"{self.domain}/api/v1/limeobject/docker_swarm/"
        response = requests.post(url=url, headers=headers, json=data)
        response.raise_for_status()
        return response

    def update_docker_swarm_object(self, application_id: str, data: dict):
        headers = {
            "x-api-key": self.api_key,
            "accept": "application/hal+json",
        }
        url = f"{self.domain}/api/v1/limeobject/docker_swarm/{application_id}/"
        response = requests.put(url=url, headers=headers, json=data)
        response.raise_for_status()
        return response
