import os
from types import SimpleNamespace
import dict_to_namespace as dtns
import json


def json_read(path_json: str) -> SimpleNamespace:
    """Legge un file json e ritorna un oggetto facilmente leggibile da python"""
    BASE_DIR = os.path.dirname(os.path.abspath(
        __file__))  # si deve decisamente trasformare in un modulo, refactor needed
    timestamp_path = os.path.join(BASE_DIR, path_json)

    with open(timestamp_path, encoding="utf-8") as f:
        return dtns.dict_to_namespace(json.load(f))
