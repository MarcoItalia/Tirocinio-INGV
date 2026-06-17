from types import SimpleNamespace


def dict_to_namespace(d: dict) -> SimpleNamespace:
    """Converte ricorsivamente un dict in un oggetto con attributi."""
    ns = SimpleNamespace()
    for key, value in d.items():
        setattr(ns, key, dict_to_namespace(value)
                if isinstance(value, dict) else value)
    return ns
