# Requisiti di sistema

---

## Rete e connettività

Il **Client** (macchina in sede INGV) è connesso tramite VPN alla rete OPENFIBER.
All'interno della rete risiede il **Server** (VM), raggiungibile dal Client via SSH.
**Solo** il Server può comunicare con la macchina di acquisizione DAS.

```
[Client INGV] ──VPN──► [Rete OPENFIBER] ──SSH──► [Server VM] ──ZMQ/SSH──► [DAS]
```

---

## Vincoli di banda

- **Server → DAS**: banda sufficiente per ricevere i dati in tempo reale nella loro interezza.
- **Client → Server**: banda insufficiente per trasmettere un file completo al secondo. I dati devono essere ridotti prima della trasmissione.

---

## Requisiti sui dati

- I dati devono essere trasmessi al Client con il **minor delay possibile** (real-time).
- Il formato di salvataggio è `.h5` (HDF5/NetCDF4).
- I file devono essere raggruppati in **blocchi da 1 minuto** per comodità di lettura.
- I dati supplementari (attributi della macchina DAS) devono essere recuperati dal Server e inclusi nei file aggregati. Dato che questi attributi cambiano raramente, il refresh è ogni **59 secondi**.

---

## Librerie Python

| Libreria   | Import utilizzato                                              | Scopo                                                    |
| ---------- | -------------------------------------------------------------- | -------------------------------------------------------- |
| `os`       | `path`, `listdir`, `remove`, `replace`, `mkdir`, `walk`        | Gestione filesystem                                      |
| `sys`      | `exit`                                                         | Terminare il programma                                   |
| `time`     | `sleep`                                                        | Attese e polling                                         |
| `paramiko` | —                                                              | Connessione SSH/SFTP al Server                           |
| `zmq`      | —                                                              | Protocollo ZeroMQ con la macchina DAS (solo Server)      |
| `netCDF4`  | `Dataset`                                                      | Lettura e scrittura file HDF5                            |
| `numpy`    | `double`, `reshape`, `ndarray`, `integer`, `floating`, `iinfo` | Manipolazione dei dati numerici                          |
| `datetime` | `datetime`, `timezone`                                         | Conversione timestamp Unix → datetime leggibile          |
| `pyyaml`   | `yaml.safe_load`, `yaml.dump`                                  | File di configurazione `.yaml`                           |
| `json`     | `load`, `dump`                                                 | Persistenza del timestamp su disco                       |
