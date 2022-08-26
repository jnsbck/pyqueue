# This file is part of pyqueue, a simple slurm like job queue written in python. pyqueue is licensed
# under the GNU General Public License v3, see <https://www.gnu.org/licenses/>. Copyright 2022 Jonas Beck

import datetime
import os
import re
import subprocess
from abc import ABC, abstractmethod
from uuid import uuid4

import psutil

from pyqueue.helpers import timedelta2dict


class Job(ABC):
    def __init__(self, id=None, priority: int = 0):
        super().__init__()
        self.id = (
            id if id is not None else str(uuid4())[:13]
        )  # numbering the jobs would be preferable
        self.status = None  # pending, running, finished, (stopped, paused), submitted
        self.owner = None  # the user that has created the job
        self.name = None  # a name that can be given to the job
        self.priority = priority  # higher priority jobs are submitted first
        self.created_at = datetime.datetime.now()  # instantiation time of job
        self._start_time = None  # time when the job was started
        self._end_time = None  # time when the job finished
        self._exit = None  # exit status of the job (0/1)
        self._out = None  # path to output file
        self._err = None  # path to err file
        self.type = self.__class__.__name__  # to identify type of job

    @abstractmethod
    def run(self):
        """Execute a cmd/script/function and return its output.

        Returns:
            returncode, stdout, stderr
        """
        pass

    @abstractmethod
    def kill(self):
        """Terminate/kill the cmd/script/function that is being run."""
        pass

    @abstractmethod
    def check_alive(self):
        """Return True if the cmd/script/function is still being run."""
        pass

    # TODO: For requing, retrying jobs
    # @property
    # def is_finished(self):
    #     return self._exit == 0 and not self.is_alive

    def __str__(self):
        """List public job attributes as a ';' seperated list."""
        items = [
            self.__class__.__name__,
            self.id,
            self.name,
            self.status,
            self.owner,
            self.priority,
            self.created_at.strftime("%H:%M:%S, %d.%m.%Y"),
        ]
        items = [str(x) if x is not None else " - " for x in items]
        t_run = list(self._get_runtime().values())
        items += [f"{t_run[0]}-{t_run[1]:02d}:{t_run[2]:02d}:{t_run[3]:02d}"]
        return "; ".join(items)

    @timedelta2dict
    def _get_runtime(self):
        t0 = self._start_time
        tfin = self._end_time
        if t0 is None:
            return datetime.timedelta(0)
        elif tfin is None:
            if self.status == "running":
                return datetime.datetime.now() - t0
            else:
                return float("nan")
        else:
            return tfin - t0

    def __eq__(self, o: object) -> bool:
        return self.__dict__ == o.__dict__


class BashJob(Job):
    def __init__(
        self,
        cmd="echo no cmd provided",
        id=None,
        priority: int = 0,
        name: str = None,
        output_dir: str = "./outputs",
    ):
        super().__init__(id, priority)
        self.cmd = cmd
        self.status = "pending"
        self.name = name if name != None else self.get_script_name(cmd)
        self.pid = None  # process id
        self.ppid = None  # parent process id

        os.makedirs(output_dir, exist_ok=True)
        self._out = os.path.join(output_dir, f"{self.name}_{self.id}.out")
        self._err = os.path.join(output_dir, f"{self.name}_{self.id}.err")

    def _byte2str(self, byte):
        try:
            byte = byte.decode("UTF-8")
        except Exception:
            pass
        finally:
            return byte

    def get_script_name(self, cmd):
        for tmpl in [
            "[a-z]+\.[a-z]+.",
            "[a-z]+.",
        ]:  # matches i.e. "script.py" or i.e. "echo "
            match = re.search(tmpl, cmd)
            if match is not None:
                break

        return match.group(0).replace(" ", "")

    def run(self):
        # use subprocess.run instead? One user suggested this
        # (https://stackoverflow.com/questions/62066599/how-to-get-the-pid-of-the-process-started-by-subprocess-run-and-kill-it)
        add_io2cmd = lambda cmd: f"{cmd} > {self._out} 2> {self._err}"
        p = subprocess.Popen(
            add_io2cmd(self.cmd),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = (self._byte2str(i) for i in p.communicate())
        self._exit = p.returncode
        return p.returncode, stdout, stderr

    def kill(self):
        # UNTESTED !!!
        parent = psutil.Process(self.pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()

    def check_alive(self):
        return (
            psutil.pid_exists(self.pid) and psutil.Process(self.pid).ppid() == self.ppid
        )
