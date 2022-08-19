import xmlrpc.client
import time

server = xmlrpc.client.ServerProxy("http://localhost:8000")

while True:
    queue = server.status()
    if len(queue) > 0:
        job = server.pop()
        print("working..")
        time.sleep(10)
    else:
        print("waiting...")
        time.sleep(1)
    # if queue empty for several minutes -> kill worker
