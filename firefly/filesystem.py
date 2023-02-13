import os

import firefly

from nxtools import PLATFORM, logging
from firefly.config import config


if PLATFORM == "windows":
    import ctypes
    import itertools
    import string

    def get_available_drives():
        drive_bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
        return list(
            itertools.compress(
                string.ascii_uppercase,
                map(lambda x: ord(x) - ord("0"), bin(drive_bitmask)[:1:-1]),
            )
        )


def load_filesystem(handler=False):
    paths: dict[int, str] = {}
    if PLATFORM == "windows":
        for letter in get_available_drives():
            if handler:
                handler(letter)
            base_path = f"{letter}:\\"
            if not os.path.exists(base_path):
                continue

            storage_ident = os.path.join(base_path, ".nebula_root")
            if not os.path.exists(storage_ident):
                continue

            for line in open(storage_ident).read().split("\n"):
                try:
                    site, id_storage = line.split(":")
                    id_storage = int(id_storage)
                except Exception:
                    continue

                if site != config.site.name:
                    continue
                paths[id_storage] = base_path

    for storage in firefly.settings.storages:
        if PLATFORM == "windows" and storage.id in paths:
            storage.path = paths[storage.id]
            logging.debug(f"Mapped storage {id_storage} to {base_path}")

        elif PLATFORM == "unix":
            path = f"/mnt/{config.site.name}_{storage.id:<02d}"
            if not os.path.isdir(path):
                continue
            storage.path = path
            logging.debug(f"Mapped storage {id_storage} to {path}")
