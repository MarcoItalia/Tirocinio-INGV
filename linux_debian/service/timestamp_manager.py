from os import path
from json import load, dump
import numpy as np


def __json_read(path_json: str) -> dict:
    """Legge un file json e ritorna un oggetto facilmente leggibile da python"""
    base_dir = path.dirname(path.abspath(
        __file__))
    timestamp_path = path.join(base_dir, path_json)

    with open(timestamp_path, encoding="utf-8") as f:
        return load(f)


def read_timestamp(path_json: str = "timestamp.json") -> np.double:
    """Legge il file dove è apposto il timestamp e ritorna il suo valore"""

    timestamp_dct = __json_read(path_json)
    return np.double(timestamp_dct["last_timestamp"])


def save_last_timestamp(timestamp, path_json: str = "timestamp.json"):
    """Salva il timestamp nel file"""

    base_dir = path.dirname(path.abspath(
        __file__))
    timestamp_path = path.join(base_dir, path_json)

    with open(timestamp_path, 'w+', encoding="utf-8") as f:
        dump({"last_timestamp": np.double(timestamp)}, f, indent=4)
