import json
import queue
import time
from typing import Any

import websocket
from PySide6.QtCore import QThread

from firefly.config import config
from firefly.log import log

if config.debug:
    websocket.enableTrace(True)


class SeismicMessage:
    def __init__(self, **payload):
        self.timestamp = time.time()
        self.site_name = config.site.name
        self.host = payload.get("host", "server")
        self.topic = payload.get("topic", "unknown")
        self.data = payload.get("data", {})

    def __getitem__(self, key: str) -> Any:
        return self.data.get(key)

    @property
    def method(self):
        # V5 compat
        return self.topic

    def __repr__(self):
        return f"<SeismicMessage {self.topic}>"


class SeismicListener(QThread):
    def __init__(self):
        QThread.__init__(self, None)
        self.site_name = config.site.name
        self.should_run = True
        self.active = False
        self.last_msg = time.time()
        self.queue = queue.Queue()
        self.start()

    def run(self):
        addr = config.site.host.replace("http", "ws", 1) + "/ws"
        while self.should_run:
            log.debug(f"[LISTENER] Connecting to {addr}", handlers=False)
            self.halted = False
            self.ws = websocket.WebSocketApp(
                addr,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
            )
            self.ws.run_forever()
            self.active = False

        log.debug("[LISTENER] halted", handlers=False)
        self.halted = True

    def on_open(self, *args):
        log.success("[LISTENER] connected", handlers=False)
        self.ws.send(
            json.dumps(
                {
                    "topic": "auth",
                    "token": config.site.token,
                    "subscribe": ["*"],
                }
            )
        )

    def on_message(self, *args):
        data = args[-1]
        if not self.active:
            log.success("[LISTENER] Got first message!", handlers=False)
            self.active = True
        try:
            original_payload = json.loads(data)
            message = SeismicMessage(**original_payload)
        except Exception:
            log.traceback(handlers=False)
            log.debug(f"[LISTENER] Malformed message: {data}", handlers=False)
            return

        self.last_msg = time.time()

        if initiator := message.data.get("initiator"):
            if message.data and initiator == config.client_id:
                return

        self.queue.put(message)

    def on_error(self, *args):
        error = args[-1]
        log.warning(error, handlers=False)

    def on_close(self, *args):
        self.active = False
        if self.should_run:
            log.warning("[LISTENER] connection interrupted", handlers=False)

    def halt(self):
        log.debug("[LISTENER] Shutting down")
        self.should_run = False
        self.ws.close()
