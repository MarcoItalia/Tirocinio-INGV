import yaml
import os
from types import SimpleNamespace
import dict_to_namespace as dtns


def yaml_read(path_yaml: str = "config.yaml") -> SimpleNamespace:
    """Legge un file yaml e ritorna un oggetto facilmente leggibile da python"""
    BASE_DIR = os.path.dirname(os.path.abspath(
        __file__))  # si protrebbe trasformare in una funzione
    config_path = os.path.join(BASE_DIR, path_yaml)

    with open(config_path, encoding="utf-8") as f:
        return dtns.dict_to_namespace(yaml.safe_load(f))


def str_constructor(config_namespace: SimpleNamespace = yaml_read()) -> SimpleNamespace:
    """"""
    return (str(config_namespace.socket.protocol) + "://" + str(config_namespace.socket.ip) +
            ":" + str(config_namespace.socket.port))
