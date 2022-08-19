from xmlrpc.server import SimpleXMLRPCServer
import sys


"""To dos:
- [ ] Only allow one server to run at a time!
- [ ] Add users
- [ ] Add priorities
- [ ] Add Worker
- [ ] Add logging
- [ ] Add error handling and exceptions
- [ ] Add tests
"""

class CtlDaemon:
    def __init__(self):
        self.queue = []

    def squeue(self):
        return self.queue

    def cancel(self, job):
        self.squeue.remove(job)
        # self.worker.kill(job)
        return True

    def submit(self, job):
        self.queue.append(job)
        # if len(queue) > 1, and no registered worker -> register new worker
        return True

    def info(self):
        return True

    def pop(self):
        return self.queue.pop()

    def register_worker(self):
        # registers worker
        pass

    def kill_worker(self):
        # remove worker
        pass


server = SimpleXMLRPCServer(("localhost", 8000))
server.register_introspection_functions()
server.register_instance(CtlDaemon())
print('Listening on localhost port 8000')
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nKeyboard interrupt received, exiting.")
    server.server_close()
    sys.exit(0)


# python3 queued.py &
# python3 queuectl.py register_worker args
# python3 queuectl.py scancel args
# python3 queuectl.py sbatch args
# python3 queuectl.py squeue args