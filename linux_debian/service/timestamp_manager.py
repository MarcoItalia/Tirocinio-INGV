from os import path
from types import SimpleNamespace
import json
import numpy as np
import dict_to_namespace as dtns


def __json_read(path_json: str) -> SimpleNamespace:
    """Legge un file json e ritorna un oggetto facilmente leggibile da python"""
    BASE_DIR = path.dirname(path.abspath(
        __file__))  # si deve decisamente trasformare in un modulo, refactor needed
    timestamp_path = path.join(BASE_DIR, path_json)

    with open(timestamp_path, encoding="utf-8") as f:
        return dtns.dict_to_namespace(json.load(f))


def read_timestamp(path_json: str = "timestamp.json") -> np.double:
    """Legge il file dove è apposto il timestamp e ritorna il suo valore"""

    timestamp_dct = __json_read(path_json)
    return np.double(timestamp_dct.last_timestamp)


def save_last_timestamp(timestamp, path_json: str = "timestamp.json"):
    """Salva il timestamp nel file"""

    BASE_DIR = path.dirname(path.abspath(
        __file__))  # si deve decisamente trasformare in un modulo, refactor needed
    timestamp_path = path.join(BASE_DIR, path_json)

    json_file = __json_read(path_json)
    json_file.last_timestamp = timestamp

    with open(timestamp_path, 'w+', encoding="utf-8") as f:
        json.dump(vars(json_file), f, indent=4)
