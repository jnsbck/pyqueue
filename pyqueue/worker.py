import datetime
import os
import time
import xmlrpc.client

from jobs import *
from utils import timedelta2dict



class Worker:
    def __init__(self, queue_server = None):
        self.current_job = None
        self.pid = os.getpid()
        self._tup = datetime.datetime.now()
        self._tidle = None
        self.queue_server = queue_server
        self.status = "idle"

    def register_with_queue_server(self, server):
        self.queue_server = server
        self.queue_server.register_worker(self.pid, {"t_up": self._tup, "status": self.status, "current_job": self.current_job})

    def show_uptime(self):
        dt = datetime.datetime.now() - self._tup
        return f"{dt.days}:{dt.hours}:{dt.minutes}:{dt.seconds}"

    @timedelta2dict
    def idletime(self):
        if self._tidle is None:
            return float("inf")
        else:
            return datetime.datetime.now() - self._tidle

    def update_worker_status(self, pid, status="idle"):
        self.current_job = pid
        self.queue_server.update_worker_status(self.pid, {"status": status, "current_job": self.current_job})
        if status == "idle":
            self._tidle = datetime.datetime.now()

    def start(self):
        while True:
            if self.queue_server.get_num_pending_jobs() > 0:
                instructions = self.queue_server.acquire_job()
                job = job_from_dict(*instructions)
                self.update_worker_status(job.id, "busy")

                newpid = os.fork()
                if newpid == 0:
                    job.run()
                    os._exit(0)
                else:
                    job.pid = newpid
                    job.ppid = self.pid
                    self.queue_server.update_job_status(
                        job.id,
                        {
                            "status": "running",
                            "pid": newpid,
                            "ppid": job.ppid,
                            "start_time": datetime.datetime.now(),
                        },
                    )
                    print(
                        f"Submitted jobID:[{job.id}] PID:[{job.pid}] CMD:[{job.cmd}]."
                    )
                time.sleep(0.5)

                # wait for child process to finish
                while self.queue_server.check_alive(job.id):
                    pid = self.queue_server.get_job_pid(job.id)
                    if pid != None:
                        os.waitpid(pid, 0)
                        time.sleep(0.5)
                    else:
                        raise ValueError("pid of job was not valid.")
                    self.queue_server.update_job_status(
                        job.id,
                        {
                            "exit": 1,
                            "status": "finished",
                            "end_time": datetime.datetime.now(),
                        },
                    )  # reset ppid/pid ?

                    # try:
                    #     self.queue_server.update_job_status(job.id, {"exit": 1, "status": "finished"})
                    #     job.run()
                    # except:
                    #     self.queue_server.update_job_status(job.id, {"exit": 0, "status": "failed"})

                self.current_job = None
                self.update_worker_status(None, "idle")
            else:
                print("waiting...")
                time.sleep(5)

            if self.idletime()["minutes"] > 1:
                # if queue empty for several minutes -> kill worker
                # deregister worker
                break
        print("No more jobs queued. Worker was shut down.")

    def kill(self):
        pass


queue_server = xmlrpc.client.self.queue_serverProxy("http://localhost:8000", allow_none=True)
worker = Worker()
worker.register_with_queue_server(queue_server)
worker.start()