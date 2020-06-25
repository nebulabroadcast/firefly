import json
import queue
import time
import websocket

from .common import *
from nx import CLIENT_ID


if config.get("debug"):
    websocket.enableTrace(True)

__all__ = ["SeismicListener"]

def readlines(f):
    buff = b""
    for ch in f.iter_content(1):
        ch = ch
        if ch == b"\n":
            yield buff.decode("ascii")
            buff = b""
        else:
            buff += ch
    yield buff.decode("ascii")


class SeismicMessage(object):
    def __init__(self, packet):
        self.timestamp, self.site_name, self.host, self.method, self.data = packet

class SeismicListener(QThread):
    def __init__(self, site_name, addr, port):
        QThread.__init__(self, None)
        self.site_name = site_name
        self.should_run = True
        self.active = False
        self.last_msg = time.time()
        self.queue = queue.Queue()
        self.start()

    def run(self):
        addr = config["hub"].replace("http", "ws", 1) + "/ws/" + config["site_name"]
        while self.should_run:
            logging.debug("Connecting listener {}".format(addr), handlers=False)
            self.halted = False
            self.ws = websocket.WebSocketApp(
                    addr,
                    on_message = self.on_message,
                    on_error = self.on_error,
                    on_close = self.on_close
                )
            self.ws.run_forever()
            self.active = False

        logging.debug("Listener halted", handlers=False)
        self.halted = True


    def on_message(self, *args):
        data = args[-1]

        if not self.active:
            logging.goodnews("Listener connected", handlers=False)
            self.active = True
        try:
            message = SeismicMessage(json.loads(data))
        except Exception:
            log_traceback(handlers=False)
            logging.debug("Malformed seismic message detected: {}".format(data), handlers=False)
            return

        if message.site_name != self.site_name:
            return

        self.last_msg = time.time()

        if message.data and message.data.get("initiator", None) == CLIENT_ID:
            return

        self.queue.put(message)

    def on_error(self, *args):
        error = args[-1]
        logging.error(error, handlers=False)

    def on_close(self, *args):
        self.active = False
        if self.should_run:
            logging.warning("WS connection interrupted", handlers=False)

    def halt(self):
        logging.debug("Shutting down listener")
        self.should_run = False
        self.ws.close()
