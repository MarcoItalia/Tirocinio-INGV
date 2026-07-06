Modulo per la lettura e scrittura di file HDF5 (formato NetCDF4).
Usato da [ZMQ_data_collector](ZMQ_data_collector) (scrittura singola), [netcdf_stitch](netcdf_stitch) (aggregazione) e [ssh_file_reader](ssh_file_reader) (lettura attributi).

---

## Funzioni di lettura

> *def read_first_variable*(group) -> Dataset:
>     Attraversa ricorsivamente i gruppi HDF5 finché trova la prima variabile. Usato internamente da `H5Stitcher`.

> *def read_attribute*(path_netcdf, attr: str = "dt"):
>     Legge un attributo nominato dal primo gruppo di un file HDF5.
>     Accetta sia un path (stringa) che un `Dataset` già aperto.
>     Usato per leggere `dt_millisec`, `Location`, `Channel_start`, ecc.

---

## Funzioni di ottimizzazione

> *def _minimize_int_type*(value) -> type:
>     Ritorna il tipo NumPy intero più piccolo che può rappresentare `value` (int8 → int16 → int32 → int64).

> *def optimize_memory*(value) -> (type, value):
>     Riduce il footprint di memoria di un valore castando al tipo più piccolo compatibile.
>     Supporta interi scalari e liste. Float e altri tipi sono restituiti invariati.
>     Usato da `H5Stitcher._initialize` per salvare gli attributi supplementari in modo compatto.

---

## Classe H5Stitcher

Incolla incrementalmente più acquisizioni HDF5 da 1 secondo in un singolo file di output.

**Utilizzo:**
```python
with Dataset("output.h5", "w") as file_write:
    stitcher = H5Stitcher(file_write, add_info=True)
    for file_path in file_list:
        with Dataset(file_path, "r") as file_read:
            stitcher.append(file_read, timestamp, dt)
```

**Costruttore** `H5Stitcher(file_write, add_info=False)`:
- Legge `config.yaml` per `data_window` (channels, overlap, location)
- Se `leave_file_untouched=True`, prende i dati così come arrivano
- Se `leave_file_untouched=False`, taglia i canali secondo `channels_start`/`channels_end` (coordinate assolute) e l'overlap
- Se il file di output contiene già un gruppo `dataset`, riprende l'append da dove era stato interrotto

**Variabili principali:**
- `channel_start`, `channel_end`: indici locali (nel chunk ricevuto) della slice da salvare
- `position`: indice temporale corrente nell'output
- `initialized`: `True` se il gruppo `dataset` è già stato creato

> *def append*(self, file_read, timestamp, dt) -> None:
>     Legge la prima variabile da `file_read` e la scrive nella posizione temporale successiva.
>     Al primo append (`not initialized`) chiama `_initialize`.
>     Al primo append in assoluto risolve gli indici canale con `_resolve_channel_range`.

> *def _resolve_channel_range*(self, dataset, src_channel_start) -> None:
>     Converte le coordinate assolute di canale (config) in indici locali nel chunk ricevuto, tenendo conto del `Channel_start` della sorgente. Clipa ai limiti reali del dataset.

> *def _initialize*(self, timestamp, dt, src_channel_start) -> None:
>     Crea il gruppo `dataset` nel file di output con tutti gli attributi (`Timestamp`, `Channel_start`, `Channel_end`, `Location`, `dt_millisec`, + attributi supplementari da `_add_info.yaml`).
>     Crea le dimensioni `Time` (unlimited) e `Channels`.
>     Crea la variabile `StrainRate` (float32).

> *def _assign*(self, dataset) -> int:
>     Scrive i dati nella variabile `StrainRate` alla posizione corrente.
>     Applica il taglio di canali e l'overlap. Ritorna il numero di righe scritte.

---

## Wrapper di compatibilità

> *def h5_file_write*(path_netcdf, file_read, timestamp, dt):
>     Writer single-shot backward-compatible. Crea un `H5Stitcher` e chiama `append` una volta sola.
>     Usato da [ZMQ_data_collector](ZMQ_data_collector) per scrivere ogni pacchetto acquisito.
