Modulo di supporto usato da [[client_ssh]]. Fornisce funzioni per controllare e gestire processi remoti su una macchina connessa via SSH.

---

## Funzioni

> *def is_script_running*(ssh, script_name) -> bool:
> 	Esegue `pgrep -f {script_name}` sulla macchina remota. Ritorna `True` se il comando produce output (script in esecuzione), `False` altrimenti.

> *def pid_script*(ssh, script_name) -> int:
> 	Ritorna il PID dello script se in esecuzione, altrimenti `0`.

> *def script_kill*(ssh, script):
> 	Termina il processo remoto. `script` può essere un intero (PID) o una stringa (nome); se stringa, risolve prima il PID con `pid_script`.

> *def start_script*(ssh, script_path):
> 	Avvia lo script Python al path indicato sulla macchina remota con `nohup`, reindirizzando stdout e stderr su `/tmp/script.log`. Il processo sopravvive alla chiusura della sessione SSH.
