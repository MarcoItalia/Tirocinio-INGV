Script principale del Server. Acquisisce dati StrainRate dalla macchina DAS tramite ZeroMQ (protocollo REQ/REP) e li salva in locale come file `.h5` in una coda FiFo.
Avvia in background il thread [ssh_file_reader](ssh_file_reader.md) per aggiornare i dati supplementari ogni `59` secondi.
Riprende l'acquisizione dall'ultimo timestamp salvato tramite [timestamp_manager](../Supports/timestamp_manager.md).

---

## Protocollo ZMQ

Il collector invia alla macchina DAS il timestamp dell'ultimo file salvato (float64).

La macchina risponde con **3 messaggi**:

> **Messaggio 1** — `[4 byte: COUNT | 8 byte: Timestamp]`
> - **COUNT**: numero di blocchi nel pacchetto. Lo script scarta se ≠ 1.
> - **Timestamp**: Unix time del dato (float64), **calcolato circa a metà del campionamento**. Per questo motivo viene ridotto e aumentato all'acquisizione e al salvataggio.

> **Messaggio 2** — `[24 byte: spacing | 24 byte: origin | 24 byte: indexes | 4 byte: unit_size]`
> - **spacing**: 3× float64 — distanza tra punti in X, Y, Z. Lo spacing Y corrisponde al `dt` (passo temporale in ms).
> - **origin**: 3× float64 — origine nella matrice interna. Non utilizzato.
> - **indexes**: 6× int32 — inizio e fine delle dimensioni X (spazio) e Y (tempo). Usati per il reshape del messaggio 3.
> - **unit_size**: byte per singolo blocco nel messaggio 3.

> **Messaggio 3** — `[N byte: float32]`
> Vettore flat che rappresenta la matrice StrainRate 2-D.
> Reshape: `(size_frequence + 1, size_dist + 1)` dove le dimensioni si ricavano dagli indici del messaggio 2.

---

## Coda FiFo

I file vengono salvati in `SAVE_PATH` con nome `{timestamp}.h5`.
Se il numero di file presenti raggiunge `QUEUE_DIM`, il pacchetto viene scartato per proteggere la memoria del Server in caso di disconnessione prolungata del Client.

---

## Classe ZmqDc

Incapsula il socket ZMQ REQ. Gestisce timeout e riconnessione automatica.

> *def create_socket*(self):
> 	Crea e connette un socket REQ con timeout (`SNDTIMEO=500ms`, `RCVTIMEO=2000ms`) e le opzioni `REQ_RELAXED` / `REQ_CORRELATE` per permettere la riconnessione senza perdere lo stato del protocollo.

> *def comunicate*(self, timestamp) -> (msg1, msg2, msg3):
> 	Invia il timestamp e riceve i 3 messaggi. 
> 	In caso di `zmq.Again` (timeout send o recv), ricrea il socket e riprova.

> [!failure]
> Solleva `ValueError` se `COUNT != 1`.
---

## Funzioni

> *def write_packet*(timestamp, strain_rate, dt):
>	Controlla la dimensione della coda. Se non è piena, scrive il file `.h5` tramite [netcdf4_h5_manager](../Supports/netcdf4_h5_manager.md).

> *def main*() -> None:
>	Crea `SAVE_PATH`, avvia il thread [ssh_file_reader](ssh_file_reader.md), legge l'ultimo timestamp da [timestamp_manager](../Supports/timestamp_manager.md) e avvia il loop di acquisizione. Per ogni pacchetto valido: reshape dei dati → `write_packet` → aggiornamento timestamp. Se i dati non sono nuovi, dorme 150ms per evitare busy-loop. Termina con `sys_exit()` se `COUNT != 1`.
