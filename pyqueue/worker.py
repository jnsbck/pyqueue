# This file is part of pyqueue, a simple slurm like job queue written in python. pyqueue is licensed
# under the GNU General Public License v3, see <https://www.gnu.org/licenses/>.

#!/usr/bin/env python3
# Copyright 2022 Jonas Beck

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import os
import time
import xmlrpc.client

from pyqueue.helpers import timedelta2dict
from pyqueue.jobs import *
from pyqueue.utils import try_unpickle


class Worker:
    def __init__(self, queue_server=None):
        self.current_job = None
        self.pid = os.getpid()
        self._tup = datetime.datetime.now()
        self._tidle = None
        self.queue_server = queue_server
        self.status = "idle"

    def register_with_queue_server(self, server):
        self.queue_server = server
        self.queue_server.register_worker(
            self.pid,
            {"t_up": self._tup, "status": self.status, "current_job": self.current_job},
        )

    def show_uptime(self):
        dt = datetime.datetime.now() - self._tup
        return f"{dt.days}:{dt.hours}:{dt.minutes}:{dt.seconds}"

    @timedelta2dict
    def idletime(self):
        if self._tidle is None:
            return datetime.timedelta(0)
        else:
            return datetime.datetime.now() - self._tidle

    def update_worker_status(self, job_id, status="idle"):
        self.current_job = job_id
        self.queue_server.update_worker_status(
            self.pid, {"status": status, "current_job": self.current_job}
        )
        if status == "idle":
            self._tidle = datetime.datetime.now()

    def start(self):
        print("Starting worker")
        assert self.queue_server != None, "No queue sever was registered."
        self.update_worker_status(None, "idle")

        while True:
            if self.queue_server.get_num_pending_jobs() > 0:
                job = self.queue_server.acquire_job()
                job = try_unpickle(job)
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
                            "_start_time": datetime.datetime.now(),
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
                            "_end_time": datetime.datetime.now(),
                        },
                    )  # reset ppid/pid ?

                    # try:
                    #     self.queue_server.update_job_status(job.id, {"exit": 1, "status": "finished"})
                    #     job.run()
                    # except:
                    #     self.queue_server.update_job_status(job.id, {"exit": 0, "status": "failed"})

                self.update_worker_status(None, "idle")
            else:
                if self.idletime()["seconds"] < 5:
                    print("Worker is currently idle and accepting jobs")
                time.sleep(5)

            if self.idletime()["minutes"] > 1:
                # if queue empty for several minutes -> kill worker
                # deregister worker
                break
        print("Worker was shut down due to inactivity.")

    def kill(self):
        pass


if __name__ == "__main__":

    # init logger
    queue_server = xmlrpc.client.ServerProxy("http://localhost:8000", allow_none=True)
    worker = Worker()
    worker.register_with_queue_server(queue_server)
    worker.start()
