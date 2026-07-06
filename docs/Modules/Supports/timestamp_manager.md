Modulo di supporto usato da [[ZMQ_data_collector]]. Gestisce la persistenza dell'ultimo timestamp acquisito in `timestamp.json`, permettendo al collector di riprendere dall'ultimo dato acquisito dopo un riavvio.

> [!info]
> La macchina DAS **NON** mantiene tutti i dati acquisiti in memoria. Nel caso in cui il timestamp sia troppo vecchio, la macchina DAS risponde con l'ultimo dato acquisito. 
---


> [!info]
> Se la macchina DAS riceve `0` come timestamp, risponde con l'ultimo dato acquisito.
---
## Funzioni

> *def read_timestamp*(path_json: str = "timestamp.json") -> np.double:
> 	Legge `timestamp.json` e ritorna il valore di `last_timestamp` come `np.double`.
> 	Se il file non esiste o contiene `0`, la macchina DAS risponde con l'ultimo dato disponibile.

> *def save_last_timestamp*(timestamp, path_json: str = "timestamp.json"):
> 	Scrive `{"last_timestamp": timestamp}` nel file JSON.
> 	Chiamato dopo ogni pacchetto acquisito con successo, prima di inviare la richiesta successiva.
