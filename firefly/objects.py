import os
import json
import time

from nxtools import logging, log_traceback

from firefly.cellformat import FireflyObject
from firefly.core.enum import ObjectStatus
from firefly.core.common import config
from firefly.core.base_objects import (
    AssetMixIn,
    ItemMixIn,
    BinMixIn,
    EventMixIn,
    UserMixIn,
)


class Asset(AssetMixIn, FireflyObject):
    pass


asset_loading = Asset()
asset_loading["title"] = "Loading..."
asset_loading["status"] = ObjectStatus.CREATING


CACHE_LIMIT = 10000


class AssetCache(object):
    def __init__(self):
        self.data = {}
        self.api = None
        self.handler = None

    def __getitem__(self, key):
        key = int(key)
        if key not in self.data:
            logging.debug("Direct loading asset id", key)
            self.request([[key, 0]])
            return Asset()
        asset = self.data[key]
        asset["_last_access"] = time.time()
        return asset

    def get(self, key):
        key = int(key)
        return self.data.get(key, Asset(meta={"title": "Loading...", "id": key}))

    def request(self, requested):
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
            logging.info(
                "Requesting data for asset(s) ID: {}".format(
                    ", ".join([str(k) for k in to_update])
                )
            )
        else:
            logging.info("Requesting data for {} assets".format(asset_count))
        self.api.get(self.on_response, objects=to_update)

    def on_response(self, response):
        if response.is_error:
            logging.error(response.message)
            return False
        ids = []
        for meta in response.data:
            try:
                id_asset = int(meta["id"])
            except KeyError:
                continue
            self.data[id_asset] = Asset(meta=meta)
            ids.append(id_asset)
        logging.debug("Updated {} assets in cache".format(len(ids)))
        if self.handler:
            self.handler(*ids)
        return True

    @property
    def cache_path(self):
        return "ffdata.{}.cache".format(config["site_name"])

    def load(self):
        if not os.path.exists(self.cache_path):
            return
        start_time = time.time()
        try:
            data = json.load(open(self.cache_path))
        except Exception:
            log_traceback("Corrupted cache file '{}'".format(self.cache_path))
            return

        for meta in data:
            self.data[int(meta["id"])] = Asset(meta=meta)
        logging.debug(
            "Loaded {} assets from cache in {:.03f}s".format(
                len(self.data), time.time() - start_time
            )
        )

    def save(self):
        if len(self.data) > CACHE_LIMIT:
            to_rm = list(self.data.keys())
            to_rm.sort(key=lambda x: self.data[x].meta.get("_last_access", 0))
            for t in to_rm[:-CACHE_LIMIT]:
                del self.data[t]

        logging.info("Saving {} assets to local cache".format(len(self.data)))
        start_time = time.time()
        data = [asset.meta for asset in self.data.values()]
        with open(self.cache_path, "w") as f:
            json.dump(data, f)
        logging.debug("Cache updated in {:.03f}s".format(time.time() - start_time))


asset_cache = AssetCache()


class Item(ItemMixIn, FireflyObject):
    @property
    def asset(self):
        if not self["id_asset"]:
            return False
        return asset_cache.get(self["id_asset"])


class Bin(BinMixIn, FireflyObject):
    pass


class Event(EventMixIn, FireflyObject):
    pass


class User(UserMixIn, FireflyObject):
    pass


user = User()


def has_right(*args, **kwargs):
    return user.has_right(*args, **kwargs)
