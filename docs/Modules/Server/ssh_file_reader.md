Thread daemon avviato da [ZMQ_data_collector](ZMQ_data_collector). Si connette via SSH/SFTP direttamente alla macchina DAS, scarica un file `.h5` completo ogni `59` secondi ed estrae gli attributi supplementari definiti in `supplement_attribute` (config). Se i valori sono cambiati, aggiorna `_add_info.yaml` e lo copia atomicamente in `SAVE_PATH` così che [netcdf_stitch](netcdf_stitch) (lato Client) possa leggerlo al prossimo ciclo di aggregazione.

> [!info]
> Lo sleep è hard-coded.
> Dato che questi dati non dovrebbero mai essere aggiornati, i `59` secondi di pausa possono essere aumentati senza problemi per ridurre il consumo di dati nella rete.
---

La directory da cui scaricare cambia ogni giorno: il path viene costruito dinamicamente con la data corrente (`YYYY-MM-DD`).

---

## Funzioni

> *def connect*(host_ip, host_port, username: str, password: str) -> (SSHClient, SFTPClient):
> 	Apre una connessione SSH con Paramiko e una sessione SFTP tunnelled. Ritorna la coppia `(client_session, sftp_session)`.

> *def file_list_from_path*(sftp_session, path_to_list: str = None) -> list:
> 	Legge una directory sulla macchina remota e ritorna la lista dei file presenti.

> *def get_server_path*(base_path: str) -> str:
> 	Costruisce il path completo aggiungendo la data odierna: `{base_path}/YYYY-MM-DD`.

> *def extract_info_dict*(path: str) -> dict:
> 	Apre il file `.h5` al path indicato e ritorna un dizionario `{attributo: valore}` per ogni chiave in `SUPP_INFO` (da `supplement_attribute` nel config).

> *def check_connection*(client_instance) -> bool:
> 	Verifica che il transport SSH sia ancora attivo tramite `send_ignore`. Ritorna `False` in caso di `EOFError`, 
> 	`OSError` o `SSHException`.

> *def dicts_are_equal*(dict1: dict, dict2: dict) -> bool:
>	Confronto sicuro tra dizionari che possono contenere `np.ndarray`. L'operatore `==` standard solleva `ValueError` su array NumPy.

> *def main*() -> None:
>	Loop infinito: costruisce il path giornaliero → scarica il file `.h5` più recente → estrae gli attributi supplementari → se diversi dall'ultimo salvataggio, aggiorna `_add_info.yaml` e lo copia atomicamente in `SAVE_PATH` → rimuove il file temporaneo → dorme 59 secondi.
>	In caso di `IOError` o `SSHException` durante il download, controlla la connessione e si riconnette se necessario.
