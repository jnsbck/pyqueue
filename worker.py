import xmlrpc.client
import time
from Jobs import *
import os
import datetime
from utils import timedelta2dict

server = xmlrpc.client.ServerProxy("http://localhost:8000", allow_none=True)

class Worker:
    def __init__(self):
        self.current_job = None
        self.pid = os.getpid()
        self._tup = datetime.datetime.now()
        self._tidle = None

    def show_uptime(self):
        dt = (datetime.datetime.now() - self._tup)
        return f"{dt.days}:{dt.hours}:{dt.minutes}:{dt.seconds}"
    
    @timedelta2dict
    def idletime(self):
        if self._tidle is None:
            return float("inf")
        else:
            return (datetime.datetime.now() - self._tidle)

    def start(self):
        while True:
            if server.get_num_pending_jobs() > 0:
                instructions = server.acquire_job()
                job = job_from_dict(*instructions)
                self.current_job = job.id

                newpid = os.fork()
                if newpid == 0:
                    job.run()
                    os._exit(0)
                else:
                    job.pid = newpid; job.ppid = self.pid
                    server.update_job_status(job.id, {"status": "running", "pid": newpid, "ppid": job.ppid, "_start_time": datetime.datetime.now()})
                    print(f"Submitted jobID:[{job.id}] PID:[{job.pid}] CMD:[{job.cmd}].")
                time.sleep(0.5)

                # wait for child process to finish
                while server.check_alive(job.id):
                    pid = server.get_pid(job.id)
                    if pid != None:
                        os.waitpid(pid, 0)
                        time.sleep(0.5)
                    else:
                        raise ValueError("pid of job was not valid.")
                    server.update_job_status(job.id, {"exit": 1, "status": "finished", "_end_time": datetime.datetime.now()}) # reset ppid/pid ?

                    # try:
                    #     server.update_job_status(job.id, {"exit": 1, "status": "finished"})
                    #     job.run()
                    # except:
                    #     server.update_job_status(job.id, {"exit": 0, "status": "failed"})
                
                    self._tidle = datetime.datetime.now()
                    self.current_job = None
            else:
                print("waiting...")
                time.sleep(5)

            if self.idletime()["minutes"] > 1:
                # if queue empty for several minutes -> kill worker
                # deregister worker
                break
        print("No more jobs queued. Worker was shut down.")


worker = Worker()
worker.start()