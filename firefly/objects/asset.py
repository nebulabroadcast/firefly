import json
import os
import time

from PySide6.QtWidgets import QApplication

import firefly
from firefly.config import config
from firefly.enum import ContentType, MediaType, ObjectStatus
from firefly.log import log

from .base import BaseObject


class Asset(BaseObject):
    object_type_id = 0
    required = ["media_type", "content_type", "id_folder"]
    defaults = {"media_type": MediaType.VIRTUAL, "content_type": ContentType.TEXT}

    def mark_in(self, new_val=False):
        if new_val:
            self["mark_in"] = new_val
        return max(float(self["mark_in"] or 0), 0)

    def mark_out(self, new_val=False):
        if new_val:
            self["mark_out"] = new_val
        return max(float(self["mark_out"] or 0), 0)

    @property
    def file_path(self):
        if self["media_type"] != MediaType.FILE:
            return ""
        if storage := firefly.settings.get_storage(self["id_storage"]):
            if not storage.path:
                return ""
            return os.path.join(storage.path, self["path"])
        return ""

    @property
    def duration(self):
        dur = float(self.meta.get("duration", 0))
        mark_in = float(self.meta.get("mark_in", 0))
        mark_out = float(self.meta.get("mark_out", 0))
        if not dur:
            return 0
        if mark_out > 0:
            dur = mark_out + (1 / self.fps)
        if mark_in > 0:
            dur -= mark_in
        return dur

    @property
    def fps(self):
        n, d = [int(k) for k in self.meta.get("fps", "25/1").split("/")]
        return n / d


asset_loading = Asset()
asset_loading["title"] = "Loading..."
asset_loading["status"] = ObjectStatus.CREATING

CACHE_LIMIT = 1000


class AssetCache:
    def __init__(self):
        self.data = {}
        self.api = None
        self.handler = None
        self.busy = False

    def __getitem__(self, key):
        key = int(key)
        if key not in self.data:
            log.debug("Direct loading asset id", key)
            self.request([[key, 0]])
            return Asset()
        asset = self.data[key]
        asset["_last_access"] = time.time()
        return asset

    def get(self, key):
        key = int(key)
        return self.data.get(key, Asset(meta={"title": "Loading...", "id": key}))

    def request(self, requested: list[tuple[int, int]], handler=None):
        self.busy = True
        to_update = []
        for id, mtime in requested:
            id = int(id)
            if id not in self.data:
                to_update.append(id)
            elif not mtime:
                to_update.append(id)
            elif self.data[id]["mtime"] < mtime:
                to_update.append(id)
        if not to_update:
            return True

        asset_count = len(to_update)
        if asset_count < 10:
            ids = ", ".join([str(k) for k in to_update])
            log.info(f"Requesting data for asset(s) ID: {ids}")
        else:
            log.info(f"Requesting data for {asset_count} assets")
        self.api.get(self.on_response, ids=to_update)

    def on_response(self, response):
        if response.is_error:
            log.error(response.message)
            self.busy = False
            return False
        ids = []
        for meta in response.data:
            try:
                id_asset = int(meta["id"])
            except KeyError:
                continue
            self.data[id_asset] = Asset(meta=meta)
            ids.append(id_asset)
        self.busy = False
        log.debug(f"Updated {len(ids)} assets in cache")
        if self.handler:
            self.handler(*ids)
        return True

    def wait(self):
        while self.busy:
            time.sleep(0.001)
            QApplication.processEvents()

    @property
    def cache_path(self):
        return f"ffdata.{config.site.name}.cache"

    def load(self):
        if not os.path.exists(self.cache_path):
            return
        start_time = time.time()
        try:
            data = json.load(open(self.cache_path))
        except Exception:
            log.traceback(f"Corrupted cache file '{self.cache_path}'")
            return

        for meta in data:
            self.data[int(meta["id"])] = Asset(meta=meta)
        elapsed = time.time() - start_time
        log.debug(f"Loaded {len(self.data)} assets from cache in {elapsed:.03f}s")

    def save(self):
        if len(self.data) > CACHE_LIMIT:
            to_rm = list(self.data.keys())
            to_rm.sort(key=lambda x: self.data[x].meta.get("_last_access", 0))
            for t in to_rm[:-CACHE_LIMIT]:
                del self.data[t]

        log.info(f"Saving {len(self.data)} assets to local cache")
        start_time = time.time()
        data = [asset.meta for asset in self.data.values()]
        with open(self.cache_path, "w") as f:
            json.dump(data, f)
        log.debug(f"Cache updated in {(time.time() - start_time):.03f}s")


asset_cache = AssetCache()
