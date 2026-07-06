Script centrale del Client. Legge la configurazione tramite [yaml_manager](../Supports/yaml_manager.md), apre una connessione SSH con Paramiko al Server e controlla se [ZMQ_data_collector](../Server/ZMQ_data_collector.md) è in esecuzione — se non lo è, lo avvia.
Crea le directory locali necessarie, avvia il thread [netcdf_stitch](netcdf_stitch.md) (daemon) e scarica continuamente i file .h5 dalla coda del Server.

I file vengono scaricati prima in un file temporaneo (`_temp_download_file`) e poi rinominati atomicamente, così che [netcdf_stitch](netcdf_stitch.md) non legga mai file parziali.
Dopo ogni download il file viene rimosso dal Server.
Gestisce anche i file `.yaml` supplementari (`_add_info.yaml`), salvandoli in `INFO_PATH`.

Se `consecutive_fails >= 60`, verifica la connessione SSH e lo stato di [ZMQ_data_collector](../Server/ZMQ_data_collector.md), riconnettendosi o riavviando lo script se necessario.

---

## Funzioni

> *def connect*(host_ip, host_port, username: str, password: str) -> (SSHClient, SFTPClient):
>	Apre una connessione SSH con Paramiko e una sessione SFTP tunnelled. Ritorna la coppia `(client, sftp_session)`.

> *def file_list_from_path*(sftp_session, path_to_list: str = None) -> list:
> 	Legge una directory sulla macchina remota e ritorna la lista dei file presenti.

> *def create_dir*(path_dir: str):
> 	Crea una directory locale. Silente se esiste già (`FileExistsError` ignorato).

> *def up_file*(list_last_timestamp, fails) -> list:
> 	Determina il prossimo file da cercare senza rileggere la directory:
> 		- Lista con >1 elementi → ritorna `lista[1:]`
> 		- Lista con 1 elemento e `fails == 0` → incrementa il timestamp nel nome (`double + 1`) e ritorna la lista aggiornata
> 		- `fails > 0` o lista vuota → ritorna la lista invariata (o `[]`)
>
> 		Il controllo su `fails` evita di incrementare troppo presto: se il file non è ancora stato acquisito dal Server è più probabile che arrivi al tentativo successivo piuttosto che esista già il timestamp successivo.

> *def get_next_file*(sftp_session, path: str, list_last_timestamp, fails) -> list:
> 	Decide la strategia per il prossimo file. Se `fails >= 2` o la lista è vuota, rilegge la directory e ordina la lista. Altrimenti delega a `up_file`.

> *def main*() -> None:
> 	Flusso principale: connessione → verifica script → creazione directory → avvio thread stitch → loop di download.
