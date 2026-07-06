Thread daemon avviato da [[client_ssh]]. Monitora la directory locale e aggrega i file .h5 da 1 secondo in file da `seconds_to_aggregate` secondi (default: `60`) usando [[netcdf4_h5_manager]].

I file successivi vengono trovati incrementando il timestamp nel nome. Il file aggregato viene scritto prima come `_stitch_incomplete.h5` e rinominato atomicamente al termine, con nome `{LOC}_{YYYYMMDD}-{HHMMSS}.h5`. I file sorgente vengono rimossi dopo l'aggregazione.

**Interruzione anticipata** (file troncati prima del completamento):
- `dt` cambiato rispetto al primo file → modalità di acquisizione cambiata
- `_add_info.yaml` cambiato → parametri dello strumento cambiati
- File non trovato per più di `MAX_CONSECUTIVE_FAILS` (10) tentativi consecutivi → Errore generico di acquisizione

---

## Funzioni

> *def dicts_are_equal*(dict1: dict, dict2: dict) -> bool:
>	Confronto sicuro tra dizionari che possono contenere `np.ndarray`. L'operatore `==` standard solleva `ValueError` su array NumPy.

> *def find_add_info*(info_path: str) -> bool:
> 	Controlla se il file `_add_info.yaml` esiste al path indicato. Ritorna `True` se trovato.

> *def wait_for_first_file*() -> str:
> 	Blocca finché non compare almeno un file `.h5` nella directory locale. Ritorna il timestamp come stringa (nome senza estensione).

> *def stitch*(timestamp_str: str, add_info_bool: bool) -> None:
> 	Aggrega i file a partire da `timestamp_str`. Al primo file legge `dt`, `Location` e `_add_info.yaml` (se `add_info_bool`). Per ogni file successivo confronta `dt` e `_add_info.yaml` con i valori del primo — in caso di discordanza tronca il file anticipatamente.

> *def main*() -> None:
> 	Crea `PATH_TO_SAVE`, attende `_add_info.yaml` se necessario, poi esegue il loop: `wait_for_first_file` → `stitch`.
