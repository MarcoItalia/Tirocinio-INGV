Modulo `yaml_manager.py`. Gestisce la lettura e scrittura di file YAML.
Usato da [ZMQ_data_collector](ZMQ_data_collector), [ssh_file_reader](ssh_file_reader), [client_ssh](client_ssh), [netcdf_stitch](netcdf_stitch) e [netcdf4_h5_manager](netcdf4_h5_manager).

Il path dei file YAML viene risolto rispetto alla directory del modulo (non dalla CWD), così lo script funziona indipendentemente da dove viene lanciato.

---

## Funzioni

> *def yaml_read*(path_yaml: str = "config.yaml") -> dict:
> 	Legge un file YAML e ritorna un dizionario Python.

> *def yaml\_write\_dict*(data: dict, path\_yaml: str = "\_add\_info.yaml"):
> 	Scrive un dizionario in un file YAML.
> 	Prima di scrivere, converte tutti i valori NumPy in tipi Python nativi tramite `_convert_to_python_vars`. Usato da [ssh_file_reader](ssh_file_reader) per persistere i dati supplementari estratti dalla macchina DAS.

> *def \_convert\_to\_python\_vars*(data: dict) -> dict:
> 	Converte ricorsivamente i valori da tipi NumPy (`np.ndarray` → `list`, `np.integer` → `int`, `np.floating` → `float`) a tipi Python nativi. Necessario perché `yaml.dump` non serializza correttamente i tipi NumPy.
