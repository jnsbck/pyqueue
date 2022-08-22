import sys
from typing import List
from xmlrpc.client import DateTime as XMLRPCDateTime
from xmlrpc.server import SimpleXMLRPCServer

from jobs import *
from utils import fix_datetime


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
        return {j.id: j for j in self.jobs}

    def get_pending_jobs(self):
        return self.get_jobs("pending")

    def get_running_jobs(self):
        return self.get_jobs("running")

    def next_job(self):
        pending_jobs = self.get_pending_jobs()
        pending_jobs = sorted(pending_jobs, key=lambda x: x.priority, reverse=True)
        job = pending_jobs.pop(0)
        job.status = "submitted"
        return job

    def remove(self, id):
        job_idx = [job.id for job in self.jobs].index(id)
        return self.jobs.pop(job_idx)

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
        self.workers = {}

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

    def update_worker_status(self, pid, kwargs):
        for key, val in kwargs.items():
            if isinstance(val, XMLRPCDateTime):
                self.workers[pid][key] = fix_datetime(val)
            else:
                self.workers[pid][key] = val

    def submit_job(self, job):
        self.queue.append(job)

    def check_alive(self, id):
        job = self.queue.get_dict()[id]
        return job.check_alive()

    def get_job_pid(self, id):
        return self.queue.get_dict()[id].pid

    # ------------------ CLIENT FUNCTIONALITY -------------------
    def sbatch(self, cmd, kwargs):
        job = BashJob(cmd)
        job.owner = kwargs["owner"] if "owner" in kwargs else None
        job.created_at = (
            fix_datetime(kwargs["timestamp"]) if "timestamp" in kwargs else None
        )
        self.submit_job(job)
        # if len(queue) > 1, and no active, worker -> register new worker

    def squeue(self):
        return self.queue.__str__()

    def scancel(self, id):
        if self.queue.get_dict()[id] == "running":
            for ppid, status in self.workers.items():
                job_id = status["current_work"]
                pid = self.get_job_pid(job_id)

                p = psutil.Process(pid)
                p.terminate()  #or p.kill()
        self.queue.remove(id)


    def sinfo(self):
        # current system info string
        # number of running, pending, etc. number of workers, ...
        pass

    def register_worker(self, pid, kwargs):
        self.workers.update({pid: kwargs})

    def kill_worker(self, pid):
        # # remove worker from self.workers
        data = self.workers.pop(pid)
        # send interupt signal to pid of worker process
        p = psutil.Process(pid)
        p.terminate()  #or p.kill()


def main():
    try:
        port = 8000
        server = SimpleXMLRPCServer(("localhost", port), allow_none=True)
    except OSError:
        raise OSError(f"Another server is already listening on port {port}")

    server.register_introspection_functions()
    server.register_instance(CtlDaemon())
    print(f"Listening on localhost port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()


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
