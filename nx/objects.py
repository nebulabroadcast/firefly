import os
import time
import copy

from nebulacore import *
from nebulacore.base_objects import *

from .connection import api
from .firefly_object import *

__all__ = ["Asset", "Item", "Bin", "Event", "User", "asset_cache"]


class Asset(AssetMixIn, FireflyObject):
    pass

class AssetCache(object):
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        key = int(key)
        if not key in self.data:
            logging.debug("Direct loading asset id", key)
            self.request([[key, 0]])
        return self.data[key]

    def request(self, requested):
        to_update = []
        for id, mtime in requested:
            id = int(id)
            if not id in self.data:
                to_update.append(id)
            elif self.data[id]["mtime"] < mtime:
                to_update.append(id)
        if not to_update:
            return True
        logging.info("Requesting data for {} assets".format(len(to_update)))
        result = api.get(ids=to_update)
        if result.is_error:
            logging.error(result.message)
            return False
        for meta in result.data:
            self.data[int(meta["id"])] = Asset(meta=meta)
        return True

    @property
    def cache_path(self):
        return "cache.{}.json".format(config["site_name"])

    def load(self):
        if not os.path.exists(self.cache_path):
            return
        start_time = time.time()
        try:
            data = json.load(open(self.cache_path))
        except:
            log_traceback("Corrupted cache file '{}'".format(self.cache_path))
            return

        for meta in data:
            self.data[int(meta["id"])] = Asset(meta=meta)
        logging.debug("Loaded {} assets from cache in {:.03f}s".format(len(self.data), time.time() - start_time))

    def save(self):
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
        return asset_cache[self["id_asset"]]

class Bin(BinMixIn, FireflyObject):
    pass

class Event(EventMixIn, FireflyObject):
    pass

class User(UserMixIn, FireflyObject):
    pass


