import time
import json
import functools

from nxtools import logging, log_traceback

from firefly.config import config
from firefly.objects import asset_cache
from firefly.version import FIREFLY_VERSION
from firefly.qt import (
    QApplication,
    QNetworkAccessManager,
    QNetworkRequest,
    QUrl,
)


class NebulaResponse:
    def __init__(self, response=200, message=None, **kwargs):
        self.dict = {"response": response, "message": message}
        self.dict.update(kwargs)

    def __repr__(self):
        return f"<NebulaResponse {self.response} {self.message}>"

    @property
    def json(self):
        return json.dumps(self.dict)

    @property
    def response(self):
        return self["response"]

    @property
    def message(self):
        return self.get("message", f"{self.response}")

    @property
    def data(self):
        return self.get("data", {})

    @property
    def is_success(self):
        return self.response < 400

    @property
    def is_error(self):
        return self.response >= 400

    def get(self, key, default=False):
        return self.dict.get(key, default)

    def __getitem__(self, key):
        return self.dict[key]

    def __len__(self):
        return self.is_success


class NebulaAPI:
    def __init__(self):
        self.manager = None
        self.queries = []

    def run(self, endpoint: str, callback, **kwargs):
        if self.manager is None:
            self.manager = QNetworkAccessManager()

        is_async = " async" if callback == -1 else ""
        logging.info(f"Executing {endpoint} request{is_async}")

        endpoint = "/api/" + endpoint
        data = json.dumps(kwargs).encode("ascii")
        access_token = config.site.token
        authorization = bytes(f"Bearer {access_token}", "ascii")
        user_agent = bytes(f"firefly/{FIREFLY_VERSION}", "ascii")

        request = QNetworkRequest(QUrl(config.site.host + endpoint))
        request.setRawHeader(b"Content-Type", b"application/json")
        request.setRawHeader(b"User-Agent", user_agent)
        request.setRawHeader(b"Authorization", authorization)
        request.setRawHeader(b"X-Client-Id", bytes(config.client_id, "ascii"))

        try:
            query = self.manager.post(request, data)
            if callback != -1:
                query.finished.connect(functools.partial(self.handler, query, callback))
            self.queries.append(query)
        except Exception:
            log_traceback()
            if callback:
                r = NebulaResponse(400, "Unable to send request")
                if callback == -1:
                    return r
                else:
                    callback(r)
            return

        if callback == -1:
            while not query.isFinished():
                time.sleep(0.0001)
                QApplication.processEvents()
            return self.handler(query, -1)

    def handler(self, response, callback):
        status = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        bytes_string = response.readAll()
        data = str(bytes_string, "utf-8")

        request = response.request()
        url = request.url().toString()

        if data:
            try:
                payload = json.loads(data)
            except Exception:
                log_traceback("Unable to parse JSON")
                print(data)
                return NebulaResponse(500, f"Unable to parse response from {url}")
        else:
            payload = {}

        message = payload.get("detail", "")
        payload.pop("detail", None)

        if status is None:
            status = 500
            message = "Unable to connect to server"
        elif status > 399:
            message = f"ERROR {status} from {url}\n\n{message}"

        result = NebulaResponse(status, message, **payload)
        self.queries.remove(response)
        if callback and callback != -1:
            callback(result)
        return result

    def __getattr__(self, endpoint: str):
        def wrapper(callback=-1, **kwargs):
            return self.run(endpoint, callback, **kwargs)

        return wrapper


api = NebulaAPI()
asset_cache.api = api
