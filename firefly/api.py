__all__ = ["api"]

import json
import queue
import functools

from nx import *
from pyqtbs import *
from nebulacore import *

from .version import FIREFLY_VERSION


class NebulaAPI():
    def __init__(self):
        self.manager = QNetworkAccessManager()
        self.queries = []


    def run(self, method, callback, **kwargs):
        logging.debug("Executing {}{} query".format("" if callback == -1 else "async ", method))
        kwargs["session_id"] = config["session_id"]
        kwargs["initiator"] = CLIENT_ID

        if method in ["ping", "login", "logout"]:
            method = "/" + method
            mime = QVariant("application/x-www-form-urlencoded")
            post_data = QUrlQuery()
            for key in kwargs:
                post_data.addQueryItem(key, kwargs[key])
            data = post_data.toString(QUrl.FullyEncoded).encode("ascii")
        else:
            method = "/api/" + method
            mime = QVariant("application/json")
            data = json.dumps(kwargs).encode("ascii")

        request = QNetworkRequest(QUrl(config["hub"] +  method))
        request.setHeader(
                QNetworkRequest.ContentTypeHeader,
                mime
            )
        request.setHeader(
                QNetworkRequest.UserAgentHeader,
                QVariant("nebula-firefly/{}".format(FIREFLY_VERSION))
            )

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
                time.sleep(.0001)
                QApplication.processEvents()
            return self.handler(query, -1)



    def handler(self, response, callback):
        er = response.error()
        if er == QNetworkReply.NoError:
            bytes_string = response.readAll()
            data = str(bytes_string, 'ascii')
            result = NebulaResponse(
                    **json.loads(data)
                )
        else:
            result = NebulaResponse(500, response.errorString())
        self.queries.remove(response)
        if callback and callback != -1:
            callback(result)
        return result



    def __getattr__(self, method_name):
        def wrapper(callback=-1, **kwargs):
            return self.run(method_name, callback, **kwargs)
        return wrapper


api = NebulaAPI()
asset_cache.api = api
