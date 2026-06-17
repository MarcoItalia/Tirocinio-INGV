from os import path
from types import SimpleNamespace
from json import load, dump
import numpy as np
import dict_to_namespace as dtns


def __json_read(path_json: str) -> SimpleNamespace:
    """Legge un file json e ritorna un oggetto facilmente leggibile da python"""
    base_dir = path.dirname(path.abspath(
        __file__))
    timestamp_path = path.join(base_dir, path_json)

    with open(timestamp_path, encoding="utf-8") as f:
        return dtns.dict_to_namespace(load(f))


def read_timestamp(path_json: str = "timestamp.json") -> np.double:
    """Legge il file dove è apposto il timestamp e ritorna il suo valore"""

    timestamp_dct = __json_read(path_json)
    return np.double(timestamp_dct.last_timestamp)


def save_last_timestamp(timestamp, path_json: str = "timestamp.json"):
    """Salva il timestamp nel file"""

    base_dir = path.dirname(path.abspath(
        __file__))
    timestamp_path = path.join(base_dir, path_json)

    json_file = __json_read(path_json)
    json_file.last_timestamp = timestamp

    with open(timestamp_path, 'w+', encoding="utf-8") as f:
        dump(vars(json_file), f, indent=4)
