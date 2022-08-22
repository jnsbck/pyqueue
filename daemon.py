from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import DateTime as XMLRPCDateTime
import sys
from typing import List
from Jobs import *
from utils import fix_datetime

"""To dos:
- [X] Only allow one server to run at a time!
- [ ] Add users
- [ ] Add priorities
- [X] Add Worker
- [ ] Add logging
- [ ] Add error handling and exceptions for jobs (Keyboard Interrupt of server / worker)
- [ ] Keep jobs in file so when Server is killed, they can potentially be resumed
- [ ] Add tests
- [ ] make sbatch work
- [ ] make sinfo nice
- [ ] make squeue nice
- [ ] make scancel work
"""

class Queue:
    def __init__(self, jobs: List[Job] = []):
        self.jobs = jobs

    def get_jobs(self, status="any"):
        if status == "any" or status == "all":
            return self.jobs
        else:
            return [job for job in self.jobs if job.status == status]

    def __getitem__(self, i):
        return self.jobs[i]

    def get_dict(self):
        return {j.id:j for j in self.jobs}

    def get_pending_jobs(self):
        return self.get_jobs("pending")
    
    def get_running_jobs(self):
        return self.get_jobs("running")

    def next_job(self):
        pending_jobs = self.get_pending_jobs()
        job = pending_jobs.pop(0)
        job.status = "submitted"
        return job

    def append(self, job):
        self.jobs.append(job)

    def has_alive(self):
        return len(self.running_jobs) > 0

    def __len__(self):
        return len(self.get_pending_jobs())

    def __str__(self):
        return "\n".join([f"{i}; " + job.__str__() for i, job in enumerate(self.jobs)])

class CtlDaemon:
    def __init__(self):
        self.queue = Queue()
        self.workers = []

    def get_num_pending_jobs(self):
        return len(self.queue)

    def get_running_ids(self):
        return [job.id for job in self.queue if job.status == "running"]

    def acquire_job(self):
        job = self.queue.next_job()
        job.status = "submitted"
        return job.__class__.__name__, job.__dict__

    def update_job_status(self, job_id, kwargs):
        job = self.queue.get_dict()[job_id]
        for key, val in kwargs.items():
            if isinstance(val, XMLRPCDateTime):
                job.__dict__[key] = fix_datetime(val)
            else:
                job.__dict__[key] = val

    def submit_job(self, job):
        self.queue.append(job)

    def check_alive(self, id):
        job = self.queue.get_dict()[id]
        return job.check_alive()

    def get_pid(self, id):
        return self.queue.get_dict()[id].pid

    # ------------------ CLIENT FUNCTIONALITY -------------------
    def sbatch(self, cmd, kwargs):
        job = BashJob(cmd)
        job.owner = kwargs["owner"] if "owner" in kwargs else None
        print(type(kwargs["timestamp"]))
        job.created_at = fix_datetime(kwargs["timestamp"]) if "timestamp" in kwargs else None
        self.submit_job(job)
        # if len(queue) > 1, and no active, worker -> register new worker

    def squeue(self):
        return self.queue.__str__()

    def scancel(self, job):
        self.squeue.remove(job)
        # self.worker.kill(job)

    def sinfo(self):
        # current system info string
        # number of running, pending, etc. number of workers, ...
        pass
    
    def register_worker(self):
        # registers worker
        pass

    def kill_worker(self):
        # remove worker
        pass

try:
    port = 8000
    server = SimpleXMLRPCServer(("localhost", port), allow_none=True)
except OSError:
    raise OSError(f"Another server is already listening on port {port}")

server.register_introspection_functions()
server.register_instance(CtlDaemon())
print(f'Listening on localhost port {port}')
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nKeyboard interrupt received, exiting.")
    server.server_close()
    sys.exit(0)


# ssh cin-hn
# python3 daemon.py &
# exit

# ssh gber3
# python3 client.py register_worker
# python3 client.py sbatch job1.sh
# python3 client.py sbatch job2.sh
# python3 client.py sbatch job3.sh
# exit

# ssh ber1
# python3 client.py register_worker
# python3 client.py sbatch job1.sh
# exit