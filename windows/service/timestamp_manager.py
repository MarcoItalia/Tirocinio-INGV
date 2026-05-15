import os
from types import SimpleNamespace
import dict_to_namespace as dtns
import json


def __json_read(path_json: str) -> SimpleNamespace:
    """Legge un file json e ritorna un oggetto facilmente leggibile da python"""
    BASE_DIR = os.path.dirname(os.path.abspath(
        __file__))  # si deve decisamente trasformare in un modulo, refactor needed
    timestamp_path = os.path.join(BASE_DIR, path_json)

    with open(timestamp_path, encoding="utf-8") as f:
        return dtns.dict_to_namespace(json.load(f))


def last_timestamp_read(path_json: str = "timestamp.json") -> int:
    """Legge il file dove è apposto il timestamp e ritorna il suo valore"""

    timestamp_dct = __json_read(path_json)
    return timestamp_dct.last_timestamp


def last_timestamp_increment(path_json: str = "timestamp.json", increment: int = 1):
    """Incrementa il last timestamp nel file. Senza specificare l'incremento, aumenta di 1"""

    BASE_DIR = os.path.dirname(os.path.abspath(
        __file__))  # si deve decisamente trasformare in un modulo, refactor needed
    timestamp_path = os.path.join(BASE_DIR, path_json)

    json_file = __json_read(path_json)
    json_file.last_timestamp += increment

    with open(timestamp_path, 'w+', encoding="utf-8") as f:
        json.dump(vars(json_file), f, indent=4)
