import time

while True:
    try:
        if input("c per uscire\t") == 'c':
            break
    except EOFError:
        pass
    time.sleep(3)
print("BB")
