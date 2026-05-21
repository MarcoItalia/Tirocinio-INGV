import time
import timestamp_manager

last_timestamp = timestamp_manager.read_timestamp()

time.sleep(2)

for i in range(10):
    try:

        # gen a document in the local dir
        with open((f"/mnt/c/users/marco/Documenti/Università/III Anno/Tirocinio/prova_da_copiare/{str(last_timestamp)}.txt"), "w+", encoding="utf-8") as f:
            f.write("Stuff " + str(last_timestamp))
        # check for permissions..

        last_timestamp += 1
        timestamp_manager.save_last_timestamp(last_timestamp)
        # if input("c per uscire: ") == 'c':
        #    break

    except EOFError:
        pass
    time.sleep(5)
print("BB")
