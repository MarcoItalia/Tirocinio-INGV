from types import SimpleNamespace
import numpy as np
from os import path
import yaml
import dict_to_namespace as dtns


def yaml_read(path_yaml: str = "config.yaml") -> SimpleNamespace:
    """Legge un file yaml e ritorna un oggetto facilmente leggibile da python"""
    base_dir = path.dirname(path.abspath(
        __file__))  # si protrebbe trasformare in una funzione
    config_path = path.join(base_dir, path_yaml)

    with open(config_path, mode="r", encoding="utf-8") as f:
        return dtns.dict_to_namespace(yaml.safe_load(f))


def yaml_write_dict(data: dict, path_yaml: str = "_add_info.yaml"):
    """Legge un file yaml e ritorna un oggetto facilmente leggibile da python"""
    base_dir = path.dirname(path.abspath(
        __file__))  # si protrebbe trasformare in una funzione
    config_path = path.join(base_dir, path_yaml)

    with open(config_path, mode="w", encoding="utf-8") as f:
        to_write = _convert_to_python_vars(data)
        yaml.dump(to_write, stream=f, default_flow_style=False)


def _convert_to_python_vars(data) -> dict:
    return_dict = {}
    for key, value in data.items():
        if isinstance(value, dict):
            return_dict[key] = _convert_to_python_vars(value)
        elif isinstance(value, np.ndarray):
            return_dict[key] = value.tolist()
        elif isinstance(value, np.integer):
            return_dict[key] = int(value)
        elif isinstance(value, np.floating):
            return_dict[key] = float(value)
        else:
            return_dict[key] = value
    return return_dict
