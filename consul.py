import json
import re

import requests


class ConsulClient:
    def __init__(self, cookie=None, consul_server=None):
        self.cookie = cookie
        self.consul_server = consul_server
        pass

    def get_kv_value(self, endpoint, return_json=True):
        url = f"https://{self.consul_server}/v1/kv/{endpoint}"
        response = requests.get(
            url,
            headers={
                "Cookie": self.cookie,
                "Accept": "application/json, text/javascript, */*; q=0.01'",
            },
        )

        if response.status_code == 200:
            if return_json:
                return json.loads(response.text)
            else:
                return response.text
        elif response.status_code == 404:
            return {}
        else:
            raise Exception(f"Failed to get value from consul: {response.status_code}")

    def get_application_config(self, application_id):
        endpoint = f"applications/{application_id}/application_config?raw"
        application_config = self.get_kv_value(endpoint=endpoint)
        return application_config

    def get_all_applications(self):
        endpoint = "applications/?keys&dc=testing&separator=%2F"
        applications = self.get_kv_value(endpoint=endpoint)
        application_ids = []
        regex = r"applications\/(.*)\/"

        for application in applications:
            matches = re.finditer(regex, application, re.MULTILINE)
            first_match = next(matches, None)
            if first_match:
                application_ids.append(first_match.group(1))

        return application_ids

    def get_applications_with_url_prefix(self):
        applications = {}
        application_ids = self.get_all_applications()
        for application_id in application_ids:
            endpoint = f"applications/{application_id}/url_prefix?raw"
            subdomain = self.get_kv_value(endpoint=endpoint, return_json=False)
            applications[subdomain] = {
                "swarm_application_id": application_id,
                "subdomain": subdomain,
            }

        return applications
