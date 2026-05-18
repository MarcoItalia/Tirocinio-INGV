import yaml
import os
from types import SimpleNamespace
import dict_to_namespace as dtns


def yaml_read(path_yaml: str = "config.yaml") -> SimpleNamespace:
    """Legge un file yaml e ritorna un oggetto facilmente leggibile da python"""
    base_dir = os.path.dirname(os.path.abspath(
        __file__))  # si protrebbe trasformare in una funzione
    config_path = os.path.join(base_dir, path_yaml)

    with open(config_path, encoding="utf-8") as f:
        return dtns.dict_to_namespace(yaml.safe_load(f))


def str_constructor(config_namespace: SimpleNamespace = yaml_read(), whois: str = "client") -> str:
    """Costruisce una stringa'protocollo://ip:porta' leggendo da un SimpleNS"""
    if whois == "client":
        return (str(config_namespace.socket.client.protocol) + "://" +
                str(config_namespace.socket.client.ip) + ":" + str(config_namespace.socket.client.port))
    elif whois == "server":
        return (str(config_namespace.socket.server.protocol) +
                "://" + str(config_namespace.socket.server.ip) + ":" + str(config_namespace.socket.server.port))
    else:
        try:
            return (str(config_namespace.socket.protocol) + "://" +
                    str(config_namespace.socket.ip) + ":" + str(config_namespace.socket.port))
        except:
            return -1
