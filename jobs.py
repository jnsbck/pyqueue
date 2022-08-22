from abc import ABC, abstractmethod
import datetime
import subprocess
import psutil
from utils import timedelta2dict, datetime2str

class Job(ABC):
    def __init__(self, priority: int = 0):
        super().__init__()
        self.id = hex(id(self))
        self.exit = None
        self.status = None # pending, running, finished, (stopped, paused), submitted
        self.owner = None
        self.priority = priority
        self.created_at = None
        self.pid = None
        self.ppid = None
        self.start_time = None
        self.end_time = None

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def kill(self):
        pass
    
    @abstractmethod
    def check_alive(self):
        pass

    # TODO: For requing, retrying jobs
    # @property
    # def is_finished(self):
    #     return self.exit == 0 and not self.is_alive

    def __str__(self):
        items = [self.__class__.__name__, self.id, self.ppid, self.pid, self.status, self.owner, self.priority, datetime2str(self.created_at)]
        items = [str(x) if x is not None else " - " for x in items]
        t_run = list(self.get_runtime().values())
        items += [f"{t_run[0]}-{t_run[1]:02d}:{t_run[2]:02d}:{t_run[3]:02d}"]
        return "; ".join(items)

    @timedelta2dict
    def get_runtime(self):
        t0 = self.start_time
        tfin = self.end_time
        if t0 is None:
            return datetime.timedelta(0)
        elif tfin is None:
            if self.status == "running":
                return datetime.datetime.now() - t0
            else:
                return float("nan")
        else:
            return tfin - t0

class BashJob(Job):
    def __init__(self, cmd, priority: int = 0):
        super().__init__(priority)
        self.cmd = cmd
        self.status = "pending"

    def _byte2str(self, byte):
        try:
            byte = byte.decode("UTF-8")
        except Exception:
            pass
        finally:
            return byte

    def run(self):
        p = subprocess.Popen(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = (self._byte2str(i) for i in p.communicate())
        self.exit = p.returncode
        return p.returncode, stdout, stderr

    def kill(self):
        # subprocess.call(f"kill -9 {self.job.pid}", shell=True, stdout=devnull, stderr=devnull)
        pass
        
    def check_alive(self):
        return psutil.pid_exists(self.pid) and psutil.Process(self.pid).ppid() == self.ppid


def job_from_dict(job_type, dict):
    if "bash" in job_type.lower():
        job = BashJob(dict["cmd"])
        job.__dict__ = dict
        return job
