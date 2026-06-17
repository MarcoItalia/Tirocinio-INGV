from types import SimpleNamespace
from os import path
import yaml
import dict_to_namespace as dtns


def yaml_read(path_yaml: str = "config.yaml") -> SimpleNamespace:
    """Legge un file yaml e ritorna un oggetto facilmente leggibile da python"""
    base_dir = path.dirname(path.abspath(
        __file__))  # si protrebbe trasformare in una funzione
    config_path = path.join(base_dir, path_yaml)

    with open(config_path, encoding="utf-8") as f:
        return dtns.dict_to_namespace(yaml.safe_load(f))
