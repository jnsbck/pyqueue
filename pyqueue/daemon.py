# This file is part of pyqueue, a simple slurm like job queue written in python. pyqueue is licensed
# under the GNU General Public License v3, see <https://www.gnu.org/licenses/>. Copyright 2022 Jonas Beck

import logging
import signal
import sys
import threading
from typing import List
from xmlrpc.client import DateTime as XMLRPCDateTime
from xmlrpc.server import SimpleXMLRPCServer

from pyqueue.helpers import dt2dict, timedeltastr
from pyqueue.jobs import *
from pyqueue.utils import check_pickle, fix_datetime, get_logger, try_unpickle

log = get_logger("DAEMON")


class Queue:
    def __init__(self, jobs: List[Job] = None):
        self.jobs = [] if jobs is None else jobs

    def get_jobs(self, status="any"):
        if status == "any" or status == "all":
            return self.jobs
        else:
            return [job for job in self.jobs if job.status == status]

    def get_dict(self):
        return {j.id: j for j in self.jobs}

    def get_pending_jobs(self):
        return self.get_jobs("pending")

    def get_running_jobs(self):
        return self.get_jobs("running")

    # def dump(self, path):
    #     pass

    # def load(self, path):
    #     pass

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

    def __getitem__(self, i):
        return self.jobs[i]

    def __call__(self):
        return self.jobs

    def __contains__(self, o):
        return o in self.jobs

    def __len__(self):
        return len(self.get_pending_jobs())

    def __str__(self, filter={"finished": False}):
        jobs = self.jobs.copy()
        for key, value in filter.items():
            if key == "finished" and not value:
                jobs = [job for job in jobs if job.status != "finished"]
            elif key == "finished" and value:
                pass
            else:
                jobs = [job for job in jobs if job.__dict__[key] == value]
        return "\n".join([f"{i}; " + job.__str__() for i, job in enumerate(jobs)])


class StoppableServer(SimpleXMLRPCServer):
    def __init__(self, port=8000):
        try:
            super().__init__(("localhost", port), allow_none=True, logRequests=False)
        except OSError:
            raise OSError(f"Another server is already listening on port {port}")

        def shutdown(kill_thread=True):
            self.server.server_close()
            # sys.exit() produces error and leaves thread running, hence kill option
            if kill_thread:
                os.kill(os.getpid(), signal.SIGTERM)
            sys.exit()

        self.register_instance(CtlDaemon())
        self.register_function(shutdown)


class StoppableServerThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, port=8000, as_daemon=True):
        self.server = StoppableServer(port)
        self.port = port

        super(StoppableServerThread, self).__init__(
            target=self.server.serve_forever, daemon=as_daemon
        )

    def stop(self):
        self.server.server_close()

    def stopped(self):
        return self.server.socket.fileno() == -1


class CtlDaemon:
    def __init__(self):
        self.queue = Queue()
        self.workers = {}

    def get_num_pending_jobs(self):
        return len(self.queue)

    def get_num_running_jobs(self):
        return len(self.get_running_ids())

    def get_num_workers(self):
        return len(self.workers)

    def get_running_ids(self):
        return [job.id for job in self.queue if job.status == "running"]

    def show_workers(self):
        msg = ""
        if self.get_num_workers() > 0:
            msg += "pid; uptime; status; current job\n"
        for worker_id, status in self.workers.items():
            msg += f"{worker_id}; "
            values = list(status.values())
            uptime = dt2dict(datetime.datetime.now() - fix_datetime(values[0]))
            values[0] = timedeltastr(uptime)
            values[-1] = " - " if values[-1] is None else values[-1]
            msg += "; ".join(values) + "\n"
        return msg

    @check_pickle
    def acquire_job(self):
        job = self.queue.next_job()
        job.status = "submitted"
        log.info(f"submitted job [ID:{job.id}]")
        return job

    def update_job_status(self, job_id, kwargs):
        job = self.queue.get_dict()[job_id]
        for key, val in kwargs.items():
            if isinstance(val, XMLRPCDateTime):
                job.__dict__[key] = fix_datetime(val)
            else:
                job.__dict__[key] = val
        log.info(f"Updated {list(kwargs.keys())} for job [ID:{job_id}]")

    def update_worker_status(self, pid, kwargs):
        for key, val in kwargs.items():
            if isinstance(val, XMLRPCDateTime):
                self.workers[pid][key] = fix_datetime(val)
            else:
                self.workers[pid][key] = val
        log.info(f"Updated {list(kwargs.keys())} for worker [PID:{pid}]")

    @check_pickle  # pickle & unpickle so it can be sent or received.
    def submit_job(self, job: Job or str):
        job = try_unpickle(job)
        assert isinstance(job, Job)
        self.queue.append(job)
        log.info(f"Added job [ID:{job.id}] to the queue")

    def check_alive(self, id):
        job = self.queue.get_dict()[id]
        return job.check_alive()

    def check_busy(self, pid):
        worker = self.workers[pid]
        return worker["status"] == "busy"

    def is_worker(self, pid):
        return pid in self.workers

    def get_job_pid(self, id):
        return self.queue.get_dict()[id].pid

    def remove_killed_workers(self):
        tracked_workers = self.workers.copy()
        for pid in tracked_workers:
            None if psutil.pid_exists(pid) else self.workers.pop(pid)
        log.info("Removed dead workers from tracking")

    # ------------------ CLIENT FUNCTIONALITY -------------------
    def sbatch(self, cmd, kwargs):
        job = BashJob(cmd)
        job.owner = kwargs["owner"] if "owner" in kwargs else None
        self.submit_job(job)
        log.info(f"Submitted batch job [ID:{job.id}] to queue")
        # if len(queue) > 1, and no active, worker -> register new worker

    def squeue(self, user_name, filter={"me": False}):
        if filter["me"]:
            filter["user"] = user_name
        filter.pop("me")
        filter["owner"] = filter.pop("user")  # job has owner, client has user
        filter["id"] = filter.pop("job")  # job has id, client has job

        # remove all flags that were not set.
        filter = {k: v for k, v in filter.items() if v is not None}

        header = (
            "; ".join(
                [
                    "idx",
                    "type",
                    "id",
                    "name",
                    "status",
                    "owner",
                    "priority",
                    "submitted",
                    "time",
                ]
            )
            + "\n"
        )
        return header + self.queue.__str__(filter=filter)

    def scancel(self, id):
        if self.queue.get_dict()[id] == "running":
            for ppid, status in self.workers.items():
                job_id = status["current_work"]
                pid = self.get_job_pid(job_id)

                p = psutil.Process(pid)
                p.terminate()  # or p.kill()
        self.queue.remove(id)

    def sinfo(self):
        self.remove_killed_workers()
        msg = "Queue daemon is currently running.\n\n"
        msg += f"{self.get_num_workers()} active workers:" + "\n"
        msg += self.show_workers() + "\n"
        msg += (
            f"There are currently {self.get_num_pending_jobs()} jobs pending and {self.get_num_running_jobs()} running."
            + "\n\n"
        )
        msg += "Ready to accept jobs."
        return msg

    def register_worker(self, pid, kwargs):
        self.workers.update({pid: kwargs})
        log.info(f"Worker process [PID {pid}] was registered with pyqueue.")

    def deregister_worker(self, pid):
        self.workers.pop(pid)
        log.info(f"Worker process [PID {pid}] was deregistered with pyqueue.")

    def kill_worker(self, pid):
        # # remove worker from self.workers
        data = self.workers.pop(pid)
        # send interupt signal to pid of worker process
        p = psutil.Process(pid)
        p.terminate()  # or p.kill()
        log.info(f"Worker process [PID:{pid}] was killed.")


def main():
    port = 8000
    server = StoppableServer()
    log.info(f"Listening on localhost port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.critical("\nKeyboard interrupt received, exiting.")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    log = get_logger(
        "DAEMON", log_level=logging.INFO
    )  # lower console logging level, if started as main
    main()
