# Introduzione

Guida alla configurazione e all'avvio del sistema di acquisizione.
Per una panoramica dei requisiti di sistema vedere [Requisiti](Requisiti).

---

## Architettura

```
[Macchina DAS] ──ZMQ──► [Server VM] ──SSH/SFTP──► [Client INGV]
                              │
                         [ssh_file_reader]
                         (dati supplementari)
```

- **Macchina DAS**: sorgente dati StrainRate. Raggiungibile solo dal Server.
- **Server**: acquisisce via ZMQ e mette i dati in una coda di file .h5.
- **Client**: scarica dalla coda e aggrega in file da 60 secondi.

---

## Configurazione

### Server — `linux_debian/service/config.yaml`

| Chiave                                        | Descrizione                                                   |
| --------------------------------------------- | ------------------------------------------------------------- |
| `socket_zmq.ip` / `port`                      | IP e porta ZMQ della macchina DAS                             |
| `socket_ssh.ip` / `port`                      | IP e porta SSH della macchina DAS (per dati supplementari)    |
| `credentials.user` / `passwd`                 | Credenziali SSH per la macchina DAS                           |
| `data_window.channels_start` / `channels_end` | Canali da mantenere (coordinate assolute)                     |
| `data_window.overlap`                         | Frequenze da rimuovere in coda ad ogni chunk                  |
| `data_window.location`                        | Luogo dove vengono raccolti i dati                            |
| `data_window.leave_file_untouched`            | Flag bool. Se `True`, ignora `channels_start/end` e `overlap` |
| `paths.save_path`                             | Directory locale dove salvare i file .h5 (coda)               |
| `paths.info_dir`                              | Directory locale dove salvare il file `_add_info.yaml`        |
| `paths.server_data_dir`                       | Path SSH dove cercare i file completi                         |
| `paths.queue_dim`                             | Numero massimo di file in coda (protezione memoria)           |
| `supplement_attribute`                        | Lista degli attributi DAS da estrarre nei dati supplementari  |

### Client — `windows/tunnel/config.yaml`

| Chiave                                        | Descrizione                                                   |
| --------------------------------------------- | ------------------------------------------------------------- |
| `socket.ip` / `port`                          | IP e porta SSH del Server                                     |
| `credentials.user` / `passwd`                 | Credenziali SSH del Server                                    |
| `paths.path_server`                           | Path sul Server dove si trova `ZMQ_data_collector.py`         |
| `paths.server_save_dir`                       | Subdirectory del Server dove sono i file .h5 da scaricare     |
| `paths.path_local`                            | Directory locale dove salvare i file scaricati                |
| `paths.complete_local_save_dir`               | Directory locale dove salvare i file aggregati                |
| `paths.info_dir`                              | Directory locale per `_add_info.yaml`                         |
| `data_window.channels_start` / `channels_end` | Canali da mantenere (coordinate assolute)                     |
| `data_window.overlap`                         | Frequenze da rimuovere in coda ad ogni chunk                  |
| `data_window.leave_file_untouched`            | Flag bool. Se `True`, ignora `channels_start/end` e `overlap` |
| `data_window.seconds_to_aggregate`            | Quanti file da 1s aggregare (default: 60)                     |
| `server_script_name`                          | Nome dello script da avviare sul Server                       |

---

## Avvio

### 1. Avvia il Client

```bash
cd windows/tunnel
python client_ssh.py
```

**`client_ssh.py`** in sequenza:
1. Si connette via SSH al Server
2. Avvia `ZMQ_data_collector.py` sul Server (se non già in esecuzione)
3. Lancia il thread [netcdf_stitch](netcdf_stitch) in background
4. Scarica i file .h5 dalla coda del Server man mano che arrivano

Il **Server** si avvia automaticamente; non è necessario avviarlo manualmente.

> [!warning]
> Il server ha bloccato dalle configurazioni la possibilità di avviare dei processi da remoto. Per questo motivo il serve **NON** si avvia automaticamente. Se le impostazioni dovessero cambiare, lo script funzionerebbe come descritto.

### 2. Output

I file aggregati vengono salvati in `complete_local_save_dir` con naming:

```
{LOC}_{YYYYMMDD}-{HHMMSS}.h5
```

dove `LOC` corrisponde ai primi 3 caratteri dell'attributo `location` nel file sorgente.

---

## Moduli

| Modulo                 | Dove gira       | Funzione                                    |
| ---------------------- | --------------- | ------------------------------------------- |
| [ZMQ_data_collector](ZMQ_data_collector) | Server          | Acquisisce dati dalla macchina DAS via ZMQ  |
| [ssh_file_reader](ssh_file_reader)    | Server (thread) | Scarica dati supplementari via SSH ogni 59s |
| [timestamp_manager](timestamp_manager)  | Server          | Persiste l'ultimo timestamp acquisito       |
| [client_ssh](client_ssh)         | Client          | Scarica file .h5 dal Server via SFTP        |
| [netcdf_stitch](netcdf_stitch)      | Client (thread) | Aggrega file da 1s in file da 60s           |
| [netcdf4_h5_manager](netcdf4_h5_manager) | Client + Server | Lettura/scrittura file HDF5                 |
| [yaml_manager](yaml_manager)     | Client + Server | Lettura/scrittura file YAML                 |
| [script_manager](script_manager)     | Client          | Gestione processi remoti via SSH            |
