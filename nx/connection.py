import json
import requests

import idna.idnadata
from multiprocessing import Queue # needed by cx_freeze

from firefly.version import FIREFLY_VERSION
from nebulacore import *

__all__ = ["api"]

headers = {
        'User-Agent': 'nebula-firefly/{}'.format(FIREFLY_VERSION),
    }

class NebulaAPI(object):
    def __init__(self, **kwargs):
        self._settings = kwargs
        self._cookies = requests.cookies.RequestsCookieJar()

    def get_user(self):
        try:
            response = requests.post(
                    self._settings["hub"] + "/ping",
                    cookies=self._cookies,
                    headers=headers,
                    timeout=config.get("timeout", 10)
                )
            self._cookies = response.cookies
            if response.status_code >= 400:
                return {
                        "response" : response.status_code,
                        "message" : "Unable to connect nebula server:\n{}".format(self._settings["hub"])
                    }
            result = json.loads(response.text)
        except Exception:
            log_traceback()
            return {"response" : 500, "message" : "Connection failed"}
        if not result["user"]:
            return {"response" : 403, "message" : "Unable to log-in"}
        return {"response" : 200, "data" : result["user"]}

    @property
    def auth_key(self):
        return self._cookies.get("session_id", "0")

    def set_auth(self, key):
        self._cookies["session_id"] = key

    def login(self, login, password):
        data = {
                "login" : login,
                "password" : password,
                "api" : 1
            }
        response = requests.post(self._settings["hub"] + "/login", data, headers=headers)
        self._cookies = response.cookies
        data = json.loads(response.text)
        return NebulaResponse(**data)

    def logout(self):
        data = {"api" : 1}
        response = requests.post(self._settings["hub"] + "/logout", data, headers=headers)
        self._cookies = response.cookies
        data = json.loads(response.text)
        return NebulaResponse(**data)

    def run(self, method, **kwargs):
        response = requests.post(
                self._settings["hub"] + "/api/" + method,
                data=json.dumps(kwargs),
                cookies=self._cookies,
                headers=headers
            )
        self._cookies = response.cookies
        if response.status_code >= 400:
            return NebulaResponse(
                    response=response.status_code,
                    message=DEFAULT_RESPONSE_MESSAGES.get(
                            response.status_code,
                            "Unknown error"
                        )
                )

        data = json.loads(response.text)
        return NebulaResponse(**data)

    def __getattr__(self, method_name):
        def wrapper(**kwargs):
            return self.run(method_name, **kwargs)
        return wrapper


api = NebulaAPI()
