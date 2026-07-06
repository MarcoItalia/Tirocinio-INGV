# Acquisizione Dati DAS — INGV / OPENFIBER

Documentazione del sistema realizzato da Marco Italia per l'acquisizione real-time di dati dalla macchina DAS nella rete protetta OPENFIBER.

---

## Architettura

```
[Client (INGV via VPN)] ──SSH/SFTP──► [Server VM (OPENFIBER)] ──ZMQ──► [Macchina DAS]
                                                  │
                                         [ssh_file_reader]
                                        (dati supplementari)
```

- **Macchina DAS**: espone dati StrainRate tramite ZeroMQ. Raggiungibile **solo** dal Server.
- **Server**: VM nella rete OPENFIBER. Raccoglie i dati via ZMQ, li salva in una coda locale di file .h5.
- **Client**: macchina INGV connessa alla rete tramite VPN. Scarica i file dal Server e li aggrega in file da 1 minuto.

---

## Prerequisiti

```
paramiko      # connessione SSH/SFTP
pyzmq         # protocollo ZeroMQ (solo Server)
netCDF4       # lettura/scrittura file HDF5
numpy         # manipolazione array
pyyaml        # lettura file di configurazione
```

---

## Struttura del progetto

| Directory | Componente |
|-----------|------------|
| `linux_debian/service/` | Script lato Server |
| `windows/tunnel/` | Script lato Client |
| `docs/` | Questa documentazione |

---

## Indice della documentazione

Per una guida all'avvio e alla configurazione: [Introduzione](Introduzione)
Per i requisiti di sistema: [Requisiti](Requisiti)

### Moduli Server (`linux_debian/service/`)

| Modulo                 | Funzione                                               |
| ---------------------- | ------------------------------------------------------ |
| [ZMQ_data_collector](ZMQ_data_collector) | Acquisisce dati dalla macchina DAS via ZeroMQ          |
| [ssh_file_reader](ssh_file_reader)    | Scarica dati supplementari dalla macchina DAS ogni 59s |


### Moduli Client (`windows/tunnel/`)

| Modulo            | Funzione                                   |
| ----------------- | ------------------------------------------ |
| [client_ssh](client_ssh)    | Scarica i file .h5 dal Server via SSH/SFTP |
| [netcdf_stitch](netcdf_stitch) | Aggrega i file da 1s in file da 60s        |

### Moduli di supporto (Client e Server)

| Modulo                 | Funzione                                       |
| ---------------------- | ---------------------------------------------- |
| [netcdf4_h5_manager](netcdf4_h5_manager) | Lettura e scrittura file HDF5                  |
| [yaml_manager](yaml_manager)       | Lettura e scrittura file YAML                  |
| [script_manager](script_manager)     | Gestione processi remoti via SSH               |
| [timestamp_manager](timestamp_manager)  | Persiste l'ultimo timestamp acquisito su disco |
