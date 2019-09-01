import os

from .common import *


if PLATFORM == "windows":
    import ctypes
    import itertools
    import string

    def get_available_drives():
        drive_bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
        return list(itertools.compress(string.ascii_uppercase,
            map(lambda x:ord(x) - ord('0'), bin(drive_bitmask)[:1:-1])))


def load_filesystem(handler=False):
    if PLATFORM == "windows":
        for letter in get_available_drives():
            if handler:
                handler(letter)
            base_path = "{}:\\".format(letter)
            if not os.path.exists(base_path):
                continue

            storage_ident = os.path.join(base_path, ".nebula_root")
            if not os.path.exists(storage_ident):
                continue

            for line in open(storage_ident).read().split("\n"):
                try:
                    site, id_storage = line.split(":")
                    id_storage = int(id_storage)
                except:
                    continue

                if site != config["site_name"]:
                    continue

                if id_storage in config["storages"]:
                    config["storages"][id_storage]["protocol"] = "local"
                    config["storages"][id_storage]["path"] = base_path
                    logging.debug("Mapped storage {} to {}".format(id_storage, base_path))
